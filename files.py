import convenience

__author__ = 'schrecknetuser'

import typing
import db_schema
import os
import config
from logger import Logger
from multiprocessing import Pool
import db_session


class FileInfo:
    def __init__(self, id: int, full_path: str, line_count: int):
        self.id = id
        self.line_count = line_count
        self.full_path = full_path


class FileInfoParam:
    def __init__(self, version_id, file_name, file_path):
        self.version_id = version_id
        self.file_name = file_name
        self.file_path = file_path


class FileReaderWorkerParam:
    def __init__(self, thread_number: int, file_info_params: typing.List[FileInfoParam]):
        self.file_info_params = file_info_params
        self.thread_number = thread_number


class ThreadedFileReader:
    def __init__(self, thread_number, file_info_params: typing.List[FileInfoParam]):

        self.thread_number = thread_number
        self.file_info_params = file_info_params

        self.engine = db_session.DatabaseEngine()
        self.session = None

    def init_session(self):
        self.session = self.engine.get_session()

    def close_session(self):
        self.engine.close_session(self.session)

    def process_file(self, file_info_param: FileInfoParam):
        count = 0
        with open(file_info_param.file_path, encoding="utf8", errors=config.error_treatment_method) as log_file:
            for line in log_file:
                count += 1
                if config.only_read_limited_number_of_lines and count == config.limited_number_of_lines_count:
                    break
                if count % config.print_count == 0:
                    Logger.log("[Thread %d] Counted %d lines in file %s" % (
                    self.thread_number, count, file_info_param.file_path))

        self.session.execute(
            db_schema.LogFile.__table__.insert().values(dict(name=file_info_param.file_name,
                                                  full_path=file_info_param.file_path,
                                                  line_count=count,
                                                  engine_version=file_info_param.version_id)))
        self.session.commit()
        Logger.log("[Thread %d] inserted file %s" % (self.thread_number, file_info_param.file_path))

    def run(self):
        self.init_session()
        for file_info_param in self.file_info_params:
            self.process_file(file_info_param)
        self.close_session()


def file_reader_worker(worker_param: FileReaderWorkerParam):
    Logger.log("file_reader_worker(): thread %d started" % worker_param.thread_number)

    processor = ThreadedFileReader(worker_param.thread_number, worker_param.file_info_params)
    processor.run()


class FileManager:
    def __init__(self, versions: typing.List[str]):
        self.versions = versions
        self.thread_limit = convenience.get_cpu_count()
        if config.files_manager_cpu_limit > 0:
            self.thread_limit = min(self.thread_limit, config.files_manager_cpu_limit)

        Logger.log("FileManager initialized")

    def fill_file_information(self):
        params = []

        engine = db_session.DatabaseEngine()
        session = engine.get_session()

        for version in self.versions:
            db_version = db_schema.EngineVersion(version=version)
            session.add(db_version)
            session.commit()
            directory_name = version
            for _, _, files in os.walk(directory_name):
                for log_file_name in files:
                    params.append(FileInfoParam(version_id=db_version.id,
                                                file_name=log_file_name,
                                                file_path=os.path.abspath(os.path.join(directory_name, log_file_name))))

        engine.close_session(session)

        file_count = len(params)
        pool = Pool(min(self.thread_limit, file_count))
        thread_number = 0
        args_collection = []
        chunk_size = int(file_count / self.thread_limit) + (file_count % self.thread_limit > 0)
        for file_list_chunk in convenience.split_list_into_chunks(params, chunk_size):
            args_collection.append(FileReaderWorkerParam(thread_number=thread_number, file_info_params=file_list_chunk))
            thread_number += 1

        Logger.log("FileManager.fill_file_information(): starting threads")
        pool.map(file_reader_worker, args_collection)
        pool.close()

        Logger.log("FileManager.fill_file_information(): threads completed reading files")

    def get_files_from_database(self) -> typing.List[FileInfo]:
        engine = db_session.DatabaseEngine()
        session = engine.get_session()

        result = [FileInfo(id=fi.id, full_path=fi.full_path, line_count=fi.line_count) for fi in
                        session.query(db_schema.LogFile)]

        engine.close_session(session)

        return result

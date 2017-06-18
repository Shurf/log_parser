import regexps
import config
from line_parser import LineParser
from logger import Logger
from multiprocessing import Pool
from db_schema import Diagnose
import convenience
import db_session

from typing import List


class DiagnoseCollection:
    def __init__(self):
        self.diagnose_collection = {}
        # 3646205
        self.diagnose_count = 0

    # @staticmethod
    def add_diagnose(self, diagnose_name, diagnose_subtype):
        if diagnose_name not in self.diagnose_collection.keys():
            self.diagnose_collection[diagnose_name] = set()
        if diagnose_subtype not in self.diagnose_collection[diagnose_name]:
            self.diagnose_collection[diagnose_name].add(diagnose_subtype)
            self.diagnose_count += 1


class ThreadedDiagnoseReader:
    def __init__(self, file_names, thread_number, result_collection):

        self.file_names = file_names
        self.thread_number = thread_number
        self.re_collection = regexps.RegexCollection.get_regex_collection_copy()
        self.result_collection = result_collection

    def parse_diagnose(self, line, re_collection):
        is_matched = 0
        file_diagnose = LineParser.get_file_diagnose(line)
        for reg in re_collection:
            if not reg.match(file_diagnose):
                continue
            is_matched += 1
            diagnose_name = reg.diagnose
            subtype = reg.subtype.strip('\r\n')

            self.result_collection.add_diagnose(diagnose_name, subtype)

            if reg.is_final:
                break

        if not is_matched:
            print("No match {}".format(line))

    def process_file(self, file_name):
        with open(file_name, encoding="utf8", errors='ignore') as log_file:
            count = 0
            # print(count)
            for line in log_file:
                count += 1
                if config.only_read_limited_number_of_lines and count == config.limited_number_of_lines_count:
                    break
                if count % config.print_count == 0:
                    Logger.log("[Thread %d] Processed %d lines from file %s" % (self.thread_number, count, file_name))

                # Skip lines with base load and etc
                if ("\\virus\\samples\\" not in line):
                    continue
                try:
                    self.parse_diagnose(line, self.re_collection)
                except IOError:
                    print(count)
                    continue

    def run(self):
        for file_name in self.file_names:
            self.process_file(file_name)


class DiagnoseReaderWorkerParam:
    def __init__(self, file_collection, thread_number):
        self.thread_number = thread_number
        self.file_collection = file_collection


def diagnose_reader_worker(worker_param: DiagnoseReaderWorkerParam):

    Logger.log("diagnose_reader_worker(): thread %d started" % worker_param.thread_number)

    collection = DiagnoseCollection()
    reader = ThreadedDiagnoseReader(worker_param.file_collection, worker_param.thread_number, collection)
    reader.run()

    returnable_result = {}
    for key in collection.diagnose_collection.keys():
        returnable_result[key] = []
        for diagnose in collection.diagnose_collection[key]:
            returnable_result[key].append(diagnose)
    return returnable_result


class DiagnoseWriterWorkerItem:
    def __init__(self, diagnose_id, diagnose_type, diagnose_subtype):
        self.diagnose_subtype = diagnose_subtype
        self.diagnose_type = diagnose_type
        self.diagnose_id = diagnose_id


class DiagnoseWriterWorkerParam:
    def __init__(self, thread_id: int, diagnoses: List[DiagnoseWriterWorkerItem]):
        self.diagnoses = diagnoses
        self.thread_id = thread_id


def diagnose_writer_worker(param: DiagnoseWriterWorkerParam):

    Logger.log("diagnose_writer_worker(): thread %d started" % param.thread_id)
    engine = db_session.DatabaseEngine()
    session = engine.get_session()

    parameters_array = []
    i = 0
    total_count = 0
    list_length = len(param.diagnoses)

    Logger.log("diagnose_writer_worker(): thread %d beginning to work (%d)" % (param.thread_id, list_length))
    for diagnose_item in param.diagnoses:
        parameters_array.append(
            dict(id=diagnose_item.diagnose_id,
                 dia_type=diagnose_item.diagnose_type,
                 subtype=diagnose_item.diagnose_subtype))
        i += 1
        total_count += 1

        if i >= config.bulk_insert_length:
            session.bulk_insert_mappings(Diagnose, parameters_array)
            session.commit()
            Logger.log("[Thread %d] inserted %d/%d diagnoses" % (param.thread_id, total_count, list_length))
            parameters_array = []
            i = 0

    if i < config.bulk_insert_length:
        session.bulk_insert_mappings(Diagnose, parameters_array)
        session.commit()
        Logger.log("[Thread %d] inserted %d/%d diagnoses" % (param.thread_id, total_count, list_length))

    engine.close_session(session)


class DiagnoseManager:
    def __init__(self, file_collection: List[str]):
        self.file_collection = file_collection
        self.thread_limit = convenience.get_cpu_count()
        if config.diagnose_manager_cpu_limit > 0:
            self.thread_limit = min(self.thread_limit, config.diagnose_manager_cpu_limit)
        self.diagnose_collection = None

    def clear_diagnose_collection(self):
        self.diagnose_collection = None

    def join_returnable_results(self, returnable_results_collection):
        self.diagnose_collection = DiagnoseCollection()
        for returnable_result in returnable_results_collection:
            for key in returnable_result.keys():
                for diagnose in returnable_result[key]:
                    self.diagnose_collection.add_diagnose(key, diagnose)

    def read_diagnoses_from_files(self):
        file_count = len(self.file_collection)
        chunk_size = int(file_count / self.thread_limit) + (file_count % self.thread_limit > 0)

        pool = Pool(min(self.thread_limit, file_count))

        i = 0
        args_collection = []
        for file_list_chunk in convenience.split_list_into_chunks(self.file_collection, chunk_size):
            args_collection.append(DiagnoseReaderWorkerParam(file_collection=file_list_chunk, thread_number=i))
            i += 1

        Logger.log("DiagnoseManager.read_diagnoses_from_files(): starting threads")
        results = pool.map(diagnose_reader_worker, args_collection)
        pool.close()

        Logger.log("DiagnoseManager.read_diagnoses_from_files(): threads completed reading files")
        self.join_returnable_results(results)
        Logger.log("DiagnoseManager.read_diagnoses_from_files(): joined returned results")
        Logger.log("DiagnoseManager.read_diagnoses_from_files(): total diagnose count: %d" %
                   self.diagnose_collection.diagnose_count)

    def create_diagnoses_in_database_threaded(self):

        args_collection = []
        diagnoses_array = []
        id = 1
        i = 0
        thread_id = 0
        chunk_size = int(self.diagnose_collection.diagnose_count / self.thread_limit) + \
                     (self.diagnose_collection.diagnose_count % self.thread_limit > 0)

        Logger.log("DiagnoseManager.create_diagnoses_in_database_threaded(): preparing")

        for diagnose in self.diagnose_collection.diagnose_collection.keys():
            for subtype in self.diagnose_collection.diagnose_collection[diagnose]:
                diagnoses_array.append(
                    DiagnoseWriterWorkerItem(diagnose_id=id, diagnose_type=diagnose, diagnose_subtype=subtype))
                id += 1
                i += 1
                if i >= chunk_size:
                    args_collection.append(DiagnoseWriterWorkerParam(thread_id=thread_id, diagnoses=diagnoses_array))
                    diagnoses_array = []
                    i = 0
                    thread_id += 1

        if len(diagnoses_array) > 0:
            args_collection.append(DiagnoseWriterWorkerParam(thread_id=thread_id, diagnoses=diagnoses_array))
        pool = Pool(self.thread_limit)

        Logger.log("DiagnoseManager.create_diagnoses_in_database_threaded(): running threads")

        pool.map(diagnose_writer_worker, args_collection)
        pool.close()

        Logger.log("DiagnoseManager.create_diagnoses_in_database_threaded(): threads finished")


    def create_diagnoses_in_database(self, session):

        parameters_array = []
        i = 0
        total_count = 0
        id = 1
        for diagnose in self.diagnose_collection.diagnose_collection.keys():
            for subtype in self.diagnose_collection.diagnose_collection[diagnose]:
                parameters_array.append(dict(id=id, dia_type=diagnose, subtype=subtype))
                i += 1
                total_count += 1
                id += 1
                if i >= config.bulk_insert_length:
                    session.bulk_insert_mappings(Diagnose, parameters_array)
                    session.commit()
                    Logger.log("create_diagnoses_in_database(): inserted %d/%d entries" % (
                        total_count, self.diagnose_collection.diagnose_count))
                    parameters_array = []
                    i = 0

        if i < config.bulk_insert_length:
            session.bulk_insert_mappings(Diagnose, parameters_array)
            session.commit()
            Logger.log("create_diagnoses_in_database(): inserted %d entries" % total_count)

import collections
import typing
from multiprocessing import Pool

import regexps
import config
import db_session
from line_parser import LineParser
from logger import Logger
from db_schema import File, assotiation_table_file_diagnose
import convenience


class DatabaseEntry:
    def __init__(self, file_path: str, diagnose_id_list: typing.List[int]):
        self.file_path = file_path
        self.diagnose_id_list = diagnose_id_list


class EntryContainer:
    def __init__(self):
        self.entries_collection = collections.OrderedDict()

    def add_entry(self, file_path, diagnose_id):
        if file_path not in self.entries_collection.keys():
            self.entries_collection[file_path] = set()
        if diagnose_id not in self.entries_collection[file_path]:
            self.entries_collection[file_path].add(diagnose_id)

    def need_pop_entry(self) -> bool:
        return len(self.entries_collection) > config.ordered_dict_max_length

    def has_elements(self) -> bool:
        return len(self.entries_collection) > 0

    def pop_entry(self) -> DatabaseEntry:
        (file_path, diagnose_ids) = self.entries_collection.popitem()
        return DatabaseEntry(file_path=file_path, diagnose_id_list=list(diagnose_ids))


class EntryWriterWorkerParam:
    def __init__(self, file_names, thread_number, diagnoses):
        self.file_names = file_names
        self.thread_number = thread_number
        self.diagnoses = diagnoses


class ThreadedEntryProcessor:
    def __init__(self, file_names, thread_number, diagnoses):

        self.file_names = file_names
        self.thread_number = thread_number
        self.re_collection = regexps.RegexCollection.get_regex_collection_copy()
        self.entry_container = EntryContainer()
        self.engine = db_session.DatabaseEngine()

        self.diagnoses = diagnoses


        self.session = None

        self.database_queue = self.init_database_queue()
        self.current_line_id = self.thread_number*config.entry_id_multiplier + 1
        self.total_inserted_entries = 0
        self.total_inserted_relations = 0

    def init_session(self):
        self.session = self.engine.get_session()

    def init_database_queue(self):
        return []

    def close_session(self):
        self.engine.close_session(self.session)

    def find_diagnose_id(self, diagnose_name, diagnose_type):
        #if self.diagnoses is None:
        #    Logger.log("[Thread %d] loading diagnoses" % (self.thread_number))
        #    self.diagnoses = self.session.query(Diagnose).all()
        #    Logger.log("[Thread %d] finished loading diagnoses" % (self.thread_number))
        #return next((d for d in self.diagnoses if d.dia_type == diagnose_name and d.subtype == diagnose_type)).id
        return self.diagnoses[diagnose_name][diagnose_type]

    def add_entry_to_database_queue(self, entry: DatabaseEntry, file_name):
        self.database_queue.append(entry)
        if len(self.database_queue) >= config.bulk_insert_length:
            self.put_entries_to_database(file_name)

    def put_entries_to_database(self, file_name):

        total_count = len(self.database_queue)

        entries_parameters_array = []
        relationships_parameters_array = []

        for database_entry in self.database_queue:
            #entries_parameters_array.append(dict(id=self.current_line_id, file_path=database_entry.file_path[:config.max_path_length]))
            entries_parameters_array.append(dict(id=self.current_line_id, file_path=database_entry.file_path))
            for diagnose_id in database_entry.diagnose_id_list:
                relationships_parameters_array.append(dict(file_id=self.current_line_id, diagnose_id=diagnose_id))
            self.current_line_id += 1

        try:
            self.session.bulk_insert_mappings(File, entries_parameters_array)
            self.session.execute(assotiation_table_file_diagnose.insert().values(relationships_parameters_array))
            self.session.commit()
        except:
            self.session.rollback()
            Logger.log("[Thread %d] got exception reading file %s" % (self.thread_number, file_name))
            for entry_parameter in entries_parameters_array:
                try:
                    #self.session.execute(File.insert().values(entry_parameter))
                    entry_parameter['file_path'] = repr(entry_parameter['file_path'])
                    self.session.bulk_insert_mappings(File, [entry_parameter])
                    self.session.commit()
                except:
                    Logger.log("[Thread %d] failed to insert file name %s" % (self.thread_number, entry_parameter['file_path']))
                    raise

            self.session.execute(assotiation_table_file_diagnose.insert().values(relationships_parameters_array))
            self.session.commit()

        self.total_inserted_entries += total_count
        self.total_inserted_relations += len(relationships_parameters_array)
        Logger.log("[Thread %d] inserted %d relationships" % (self.thread_number, self.total_inserted_relations))
        Logger.log("[Thread %d] inserted %d entries" % (self.thread_number, self.total_inserted_entries))

        self.database_queue = self.init_database_queue()

    def parse_line(self, line, re_collection):
        is_matched = 0
        file_name = LineParser.get_file_path(line)
        file_diagnose = LineParser.get_file_diagnose(line)
        for reg in re_collection:
            if not reg.match(file_diagnose):
                continue
            is_matched += 1
            diagnose_name = reg.diagnose
            subtype = reg.subtype.strip('\r\n')

            diagnose_id = self.find_diagnose_id(diagnose_name, subtype)
            self.entry_container.add_entry(file_name, diagnose_id)

            if reg.is_final:
                break

        if not is_matched:
            print("No match {}".format(line))

    def process_file(self, file_name):
        with open(file_name, encoding="utf8", errors='replace') as log_file:
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
                    self.parse_line(line, self.re_collection)
                    while self.entry_container.need_pop_entry():
                        self.add_entry_to_database_queue(self.entry_container.pop_entry(), file_name)
                except IOError:
                    print(count)
                    continue

        while self.entry_container.has_elements():
            self.add_entry_to_database_queue(self.entry_container.pop_entry(), file_name)

    def run(self):

        self.init_session()
        current_file_name = None

        for file_name in self.file_names:
            current_file_name = file_name
            self.process_file(file_name)

        self.put_entries_to_database(current_file_name)
        self.close_session()


def entry_writer_worker(worker_param: EntryWriterWorkerParam):

    Logger.log("entry_writer_worker(): thread %d started" % worker_param.thread_number)

    """own_diagnoses = {}
    for diagnose_type in worker_param.diagnoses.keys():
        own_diagnoses[diagnose_type] = {}
        for diagnose_subtype in worker_param.diagnoses[diagnose_type].keys():
            own_diagnoses[diagnose_type][diagnose_subtype] = worker_param.diagnoses[diagnose_type][diagnose_subtype]"""
    processor = ThreadedEntryProcessor(worker_param.file_names, worker_param.thread_number, worker_param.diagnoses)
    processor.run()


class DiagnoseInfo:
    def __init__(self, id, dia_type, subtype):
        self.id = id
        self.dia_type = dia_type
        self.subtype = subtype


class EntryManager:
    def __init__(self, file_collection: typing.List[str], diagnoses):
        self.file_collection = file_collection
        self.diagnoses = diagnoses
        self.thread_limit = convenience.get_cpu_count()
        if config.entries_manager_cpu_limit > 0:
            self.thread_limit = min(self.thread_limit, config.entries_manager_cpu_limit)
        Logger.log("EntryManager initialized")

    def read_entries_from_files(self):
        file_count = len(self.file_collection)
        chunk_size = int(file_count / self.thread_limit) + (file_count % self.thread_limit > 0)

        pool = Pool(min(self.thread_limit, file_count))

        i = 0
        args_collection = []
        for file_list_chunk in convenience.split_list_into_chunks(self.file_collection, chunk_size):
            args_collection.append(EntryWriterWorkerParam(file_names=file_list_chunk, thread_number=i, diagnoses=self.diagnoses))
            i += 1

        Logger.log("EntryManager.read_entries_from_files(): starting threads")
        results = pool.map(entry_writer_worker, args_collection)
        pool.close()

        Logger.log("EntryManager.read_entries_from_files(): threads completed reading files")


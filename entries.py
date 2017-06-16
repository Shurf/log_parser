import regexps
import config
import collections
import typing
from line_parser import LineParser


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

    def pop_entry(self) -> DatabaseEntry:
        (file_path, diagnose_ids) = self.entries_collection.popitem()
        return DatabaseEntry(file_path=file_path, diagnose_id_list=list(diagnose_ids))


class ThreadedEntryProcessor:
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

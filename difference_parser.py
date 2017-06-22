__author__ = 'schrecknetuser'

import db_session
from db_schema import EngineVersion, Difference, LogEntry
from logger import Logger


class DiagnoseInfo:
    def __init__(self, diagnose_info, diagnose_subtype):
        self.diagnose_info = diagnose_info
        self.diagnose_subtype = diagnose_subtype

    def __eq__(self, other):
        """Override the default Equals behavior"""
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return False


class DifferenceInfo:
    def __init__(self, file_name, diagnose_collection):
        self.diagnose_collection = diagnose_collection
        self.file_name = file_name


class DifferenceParser:
    def __init__(self, base_engine):
        self.base_engine = base_engine
        self.engine = db_session.DatabaseEngine()
        # self.difference_list = []
        self.different_files = {}
        self.sorted_engine_ids = []
        self.sorted_engine_versions = []

    def fill_structures(self):
        session = self.engine.get_session()

        base_db_engine = session.query(EngineVersion).filter(EngineVersion.version == self.base_engine).first()
        engine_ids = [e.id for e in session.query(EngineVersion).all()]
        engine_ids.remove(base_db_engine.id)

        self.sorted_engine_ids.append(base_db_engine.id)
        self.sorted_engine_ids += sorted(engine_ids)

        self.sorted_engine_versions = []
        for id in self.sorted_engine_ids:
            self.sorted_engine_versions.append(
                session.query(EngineVersion).filter(EngineVersion.id == id).first().version)

        differences = session.query(Difference).all()

        one_percent = (int)(len(differences) / 100)
        i = 0
        for difference in differences:

            first_engine_entry = session.query(LogEntry).filter(LogEntry.id == difference.entry_id1).first()
            second_engine_entry = session.query(LogEntry).filter(LogEntry.id == difference.entry_id2).first()

            if first_engine_entry.file_path in self.different_files.keys():
                continue
            self.different_files[first_engine_entry.file_path] = {}

            for engine_id in self.sorted_engine_ids:
                self.different_files[first_engine_entry.file_path][engine_id] = []

            first_engine_detects = first_engine_entry.diagnose
            second_engine_detects = second_engine_entry.diagnose

            self.different_files[first_engine_entry.file_path][difference.engine_id1] = \
                [DiagnoseInfo(d.dia_type, d.subtype) for d in first_engine_detects]

            self.different_files[first_engine_entry.file_path][difference.engine_id2] = \
                [DiagnoseInfo(d.dia_type, d.subtype) for d in second_engine_detects]

            i += 1
            if i % one_percent == 0:
                Logger.log("processed: %d%% entries" % (i / one_percent))



        self.engine.close_session(session)

    def print_results(self):

        f = open("output.html", "w", encoding='utf-8')
        f.write("<html><body>\n")
        f.write("<table>\n")
        f.write("<tr>\n")
        f.write("<th>Filename</th>\n")
        f.write("<th>Diagnoses unique for engine %s</th>\n" % self.sorted_engine_versions[0])
        f.write("<th>Diagnoses unique for engine %s</th>\n" % self.sorted_engine_versions[1])
        f.write("<th>Common diagnoses</th>\n")
        f.write("</tr>\n")

        for file_name in self.different_files.keys():

            first_version_diagnoses = self.different_files[file_name][self.sorted_engine_ids[0]]
            second_version_diagnoses = self.different_files[file_name][self.sorted_engine_ids[1]]

            common_diagnoses = []

            unique_first_version_diagnoses = []
            unique_second_version_diagnoses = []

            for first_version_diagnose in first_version_diagnoses:
                if first_version_diagnose in second_version_diagnoses:
                    if first_version_diagnose not in common_diagnoses:
                        common_diagnoses.append(first_version_diagnose)
                    continue
                unique_first_version_diagnoses.append(first_version_diagnose)

            for second_version_diagnose in second_version_diagnoses:
                if second_version_diagnose in first_version_diagnoses:
                    if second_version_diagnose not in common_diagnoses:
                        common_diagnoses.append(second_version_diagnose)
                    continue
                unique_second_version_diagnoses.append(second_version_diagnose)

            f.write("<tr>\n")
            f.write("<td>")
            f.write(file_name)
            f.write("</td>\n")
            f.write("<td>")
            f.write("<br />".join(
                "[%s]&nbsp%s" % (f.diagnose_info, f.diagnose_subtype) for f in unique_first_version_diagnoses))
            f.write("</td>\n")
            f.write("<td>")
            f.write("<br />".join(
                "[%s]&nbsp%s" % (f.diagnose_info, f.diagnose_subtype) for f in unique_second_version_diagnoses))
            f.write("</td>\n")
            f.write("<td>")
            f.write("<br />".join(
                "[%s]&nbsp%s" % (f.diagnose_info, f.diagnose_subtype) for f in common_diagnoses))
            f.write("</td>\n")
            f.write("</tr>\n")

        f.write("</table>\n")
        f.write("</body></html>")
        f.close()


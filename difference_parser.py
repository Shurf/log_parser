__author__ = 'schrecknetuser'

import db_session
from db_schema import EngineVersion, Difference, LogEntry
from logger import Logger

class DiagnoseInfo:
    def __init__(self, diagnose_info, diagnose_subtype):
        self.diagnose_info = diagnose_info
        self.diagnose_subtype = diagnose_subtype


class DifferenceInfo:
    def __init__(self, file_name, diagnose_collection):
        self.diagnose_collection = diagnose_collection
        self.file_name = file_name


class DifferenceParser:
    def __init__(self, base_engine):
        self.base_engine = base_engine
        self.engine = db_session.DatabaseEngine()
        self.difference_list = []

    def fill_structures(self):
        session = self.engine.get_session()

        base_db_engine = session.query(EngineVersion).filter(EngineVersion.version==self.base_engine).first()
        lost_detects = session.query(Difference).filter(Difference.engine_id1==base_db_engine.id).all()

        Logger.log("total: %d" % len(lost_detects))

        i = 0
        for lost_detect in lost_detects:
            base_engine_entry = session.query(LogEntry).filter(LogEntry.id==lost_detect.entry_id1).first()
            new_engine_entry = session.query(LogEntry).filter(LogEntry.id==lost_detect.entry_id2).first()

            base_engine_detects = base_engine_entry.diagnose
            new_engine_detects = new_engine_entry.diagnose

            lost_diagnoses = []

            for base_engine_detect in base_engine_detects:
                if base_engine_detect in new_engine_detects:
                    continue
                lost_diagnoses.append(DiagnoseInfo(base_engine_detect.dia_type, base_engine_detect.subtype))
            self.difference_list.append(DifferenceInfo(base_engine_entry.file_path, lost_diagnoses))

            Logger.log("current: %d" % i)
            i += 1

        self.engine.close_session(session)

    def print_results(self):
        for difference in self.difference_list:
            print("%s" % difference.file_name)
            for diagnose in difference.diagnose_collection:
                print("%s:%s" % (diagnose.diagnose_info, diagnose.diagnose_subtype))
            print("")
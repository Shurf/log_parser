import os

import db_session
import logger
from db_schema import Diagnose
from diagnoses import DiagnoseManager
from entries import EntryManager


def log(message):
    # print(time.strftime("%H:%M:%S") + ": " + message)
    logger.Logger.log(message)



def make_core_version_from_dirname(dirname):
    return dirname.strip('/').strip('\\')


def main(session, versions):
    log("main() entered")
    file_collection = []

    for version in versions:
        dirname = version
        for _, _, files in os.walk(dirname):
            for log_file_name in files:
                file_collection.append((os.path.join(dirname, log_file_name)))

    """diagnose_manager = DiagnoseManager(file_collection=file_collection)
    diagnose_manager.read_diagnoses_from_files()
    diagnose_manager.create_diagnoses_in_database_threaded()"""

    diagnoses_dict = {}

    for diagnose in session.query(Diagnose):
        if diagnose.dia_type not in diagnoses_dict.keys():
            diagnoses_dict[diagnose.dia_type] = {}
        diagnoses_dict[diagnose.dia_type][diagnose.subtype] = diagnose.id

    entry_manager = EntryManager(file_collection=file_collection, diagnoses=diagnoses_dict)
    entry_manager.read_entries_from_files()

    log("main(): completed")


if __name__ == '__main__':
    # versions = sys.argv[1:]
    versions = ['7.00.27.02270', '7.00.30.03210']

    engine = db_session.DatabaseEngine()
    #engine.recreate_database()
    #engine.create_tables()

    session = engine.get_session()

    main(session, versions)

    engine.close_session(session)

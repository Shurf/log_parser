import db_session
import logger
from db_schema import Diagnose
from diagnoses import DiagnoseManager
from entries import EntryManager
from files import FileManager
import config
import result_table_maker


def log(message):
    # print(time.strftime("%H:%M:%S") + ": " + message)
    logger.Logger.log(message)



def make_core_version_from_dirname(dirname):
    return dirname.strip('/').strip('\\')


def main(versions):

    log("main() entered")

    file_manager = FileManager(versions=versions)
    if not config.skip_preparations and not config.skip_initial_data_fill:
        file_manager.fill_file_information()
    files = file_manager.get_files_from_database()

    if not config.skip_preparations and not config.skip_initial_data_fill:
        diagnose_manager = DiagnoseManager(file_collection=files)
        diagnose_manager.read_diagnoses_from_files()
        diagnose_manager.create_diagnoses_in_database_threaded()

    if not config.skip_initial_data_fill:
        diagnoses_dict = {}

        engine = db_session.DatabaseEngine()
        session = engine.get_session()

        for diagnose in session.query(Diagnose):
            if diagnose.dia_type not in diagnoses_dict.keys():
                diagnoses_dict[diagnose.dia_type] = {}
            diagnoses_dict[diagnose.dia_type][diagnose.subtype] = diagnose.id

        engine.close_session(session)

        entry_manager = EntryManager(file_collection=files, diagnoses=diagnoses_dict)
        entry_manager.read_entries_from_files()

    result_table_maker.ResultTableMaker().make_results()

    log("main(): completed")


if __name__ == '__main__':
    # versions = sys.argv[1:]
    versions = ['7.00.27.02270', '7.00.30.03210']

    engine = db_session.DatabaseEngine()
    if not config.skip_preparations and not config.skip_initial_data_fill:
        engine.recreate_database()
        engine.create_tables()

    main(versions)


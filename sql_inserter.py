import os
import time
import db_session

import config
import logger
from db_schema import EngineVersion
from diagnoses import DiagnoseManager


def log(message):
    # print(time.strftime("%H:%M:%S") + ": " + message)
    logger.Logger.log(message)


def create_if_not_exists(session, model, **kwargs):
    instance = model(**kwargs)
    try:
        session.add(instance)
        session.commit()
        return instance, True
    except:
        instance = session.query(model).filter_by(**kwargs).first()
        return instance, False


# if instance:
#        return instance, False
#    else:
#        instance = model(**kwargs)
#        session.add(instance)
#        # session.commit()
#        return instance, True

#    instance = session.query(model).filter_by(**kwargs).first()
#    if instance:
#        return instance, False
#    else:
#        instance = model(**kwargs)
#        session.add(instance)
#        # session.commit()
#        return instance, True

diagnose_dict = {}


def make_core_version_from_dirname(dirname):
    return dirname.strip('/').strip('\\')


def parse_tail(session, line, re_collection, core_version):
    is_matched = 0
    file_diagnose = get_file_diagnose(line)
    for reg in re_collection:
        # if reg.match(line):
        if reg.match(file_diagnose):
            is_matched += 1
            diagnose_name = reg.diagnose
            subtype = reg.subtype.strip('\r\n')
            if diagnose_name not in diagnose_dict.keys():
                diagnose_dict[diagnose_name] = set()
            if subtype not in diagnose_dict[diagnose_name]:
                diagnose_dict[diagnose_name].add(subtype)
            """diagnose, created = create_if_not_exists(session,
                                                     Diagnose,
                                                     dia_type=diagnose_name,
                                                     subtype=subtype
                                                     )
            #if created:
            #    session.commit()

            full_line, created = create_if_not_exists(session,
                                                      FullLine,
                                                      text=tail
                                                      )
            #if created:
            #    session.commit()

            file_path = get_file_path(tail)
            sample_file, created = create_if_not_exists(session,
                                                        File,
                                                        file_path=file_path,
                                                        engine_version=core_version.id
                                                        )
            sample_file.diagnose.append(diagnose)
            sample_file.full_line.append(full_line)
            if created:
                session.add(sample_file)
            else:
                session.merge(sample_file)
            session.merge(core_version)"""
            if reg.is_final:
                break

    if not is_matched:
        print("No match {}".format(line))
        # return diagnose, filepath


def parse_logs(session, dirname, re_collection):
    core_version_str = make_core_version_from_dirname(dirname)
    core_version, _ = create_if_not_exists(session, EngineVersion, version=core_version_str)
    print(time.strftime("%H:%M:%S"))
    for _, _, files in os.walk(dirname):
        for log_file_name in files:
            print(os.path.join(dirname, log_file_name))
            with open(os.path.join(dirname, log_file_name), encoding="utf8", errors='ignore') as log_file:
                count = 0
                # print(count)
                for line in log_file:
                    count += 1
                    if config.only_read_limited_number_of_lines and count == config.limited_number_of_lines_count:
                        break
                    if count % config.print_count == 0:
                        print(count)
                        print(time.strftime("%H:%M:%S"))
                        diagnose_count = 0
                        for key in diagnose_dict.keys():
                            diagnose_count += len(diagnose_dict[key])
                            # print("keys count = %d, diagnose_count = %d" % (len(diagnose_dict.keys()), diagnose_count))
                            # print("diagnoses to total count ratio: %f" % (float(diagnose_count)/total_count))
                    # Skip lines with base load and etc
                    if ("\\virus\\samples\\" not in line):
                        continue
                    try:
                        parse_tail(session, line, re_collection, core_version)
                    except IOError:
                        print(count)
                        continue
                        # session.commit()"""

    print(time.strftime("%H:%M:%S"))


def main(session, versions):
    log("main() entered")
    file_collection = []

    for version in versions:
        dirname = version
        for _, _, files in os.walk(dirname):
            for log_file_name in files:
                file_collection.append((os.path.join(dirname, log_file_name)))

    diagnose_manager = DiagnoseManager(file_collection=file_collection)
    diagnose_manager.read_diagnoses_from_files()
    #diagnose_manager.create_diagnoses_in_database(session=session)
    diagnose_manager.create_diagnoses_in_database_threaded()#6296

    log("main(): completed")


if __name__ == '__main__':
    # versions = sys.argv[1:]
    versions = ['7.00.27.02270', '7.00.30.03210']

    db_session.DatabaseEngine.recreate_database()
    db_session.DatabaseEngine.create_tables()
    session = db_session.DatabaseEngine.get_session()

    main(session, versions)

    db_session.DatabaseEngine.close_session(session)

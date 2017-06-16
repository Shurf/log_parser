from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db_schema import Base, EngineVersion, File, Diagnose


def main(session):
    old_engine, new_engine = session.query(EngineVersion).all()

    if old_engine.version > new_engine.version:
        tmp = new_engine
        new_engine = old_engine
        old_engine = tmp

    for new_sample_file in session.query(File).filter_by(engine_version=new_engine.id):
        old_sample_file = session.query(File).filter_by(engine_version=old_engine.id,
                                                          file_path=new_sample_file.file_path).first()
        if old_sample_file:
            if old_sample_file.diagnose != new_sample_file.diagnose:
                message = "Core Version: {} \n Scan Log: {} \n Core Version: {} \nScan Log: {} \n \n".format(old_engine.version,
                                                                                                             old_sample_file.full_line,
                                                                                                             new_engine.version,
                                                                                                             new_sample_file.full_line
                                                                                                             )
                print(message)

        else:
            print("Sample scanned only in new version" + new_sample_file)




if __name__ == '__main__':
    echo = False

    #for python 3.6 on windows we need to install mysqlclient package
    engine = create_engine('mysql://root:root@localhost/', echo=echo)
    engine.execute("USE scan_logs")
    Base.metadata.create_all(engine)

    session = sessionmaker(bind=engine)()

    main(session)

    session.close()

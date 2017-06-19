from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_schema import Base

class DatabaseEngine:
    def __init__(self):
        self.database_engine = None

    def get_engine(self):
        echo = False
        if self.database_engine is None:
            #self.database_engine = create_engine('mysql://root@localhost/', echo=echo)
            self.database_engine = create_engine('mysql://root:root@localhost/?charset=utf8', echo=echo)
        return self.database_engine

    def recreate_database(self):
        try:
            self.get_engine().execute("DROP DATABASE scan_logs1")
        except:
            pass
        self.get_engine().execute("CREATE DATABASE scan_logs1 COLLATE = 'utf8_bin' CHARACTER SET = 'utf8'")

    def initialize_engine(self):
        self.get_engine().execute("USE scan_logs1")

    def create_tables(self):
        self.initialize_engine()
        Base.metadata.create_all(self.get_engine())

    def get_session(self):
        self.initialize_engine()
        session = sessionmaker(bind=self.get_engine())()
        session.execute("SET NAMES utf8")
        session.execute("SET CHARACTER SET utf8")
        session.execute("SET character_set_connection=utf8")
        return session

    def close_session(self, session):
        session.close()
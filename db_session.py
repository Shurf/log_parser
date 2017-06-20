from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_schema import Base
import config

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
            self.get_engine().execute("DROP DATABASE %s" % config.db_schema_name)
        except:
            pass
        self.get_engine().execute("CREATE DATABASE %s DEFAULT CHARACTER SET utf8 DEFAULT COLLATE utf8_bin" % config.db_schema_name)

    def initialize_engine(self):
        self.get_engine().execute("USE %s" % config.db_schema_name)

    def create_tables(self):
        self.initialize_engine()
        Base.metadata.create_all(self.get_engine())

    def get_session(self):
        self.initialize_engine()
        session = sessionmaker(bind=self.get_engine(), autoflush=True)()
        session.execute("SET NAMES utf8")
        session.execute("SET CHARACTER SET utf8")
        session.execute("SET character_set_connection=utf8")
        return session

    def close_session(self, session):
        session.close()
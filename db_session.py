from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db_schema import Base

class DatabaseEngine:
    database_engine = None

    @staticmethod
    def get_engine():
        echo = False
        if DatabaseEngine.database_engine is None:
            #DatabaseEngine.database_engine = create_engine('mysql+cymysql://root@localhost/', echo=echo)
            DatabaseEngine.database_engine = create_engine('mysql://root:root@localhost/', echo=echo)
        return DatabaseEngine.database_engine

    @staticmethod
    def recreate_database():
        DatabaseEngine.get_engine().execute("DROP DATABASE scan_logs")
        DatabaseEngine.get_engine().execute("CREATE DATABASE IF NOT EXISTS scan_logs")

    @staticmethod
    def initialize_engine():
        DatabaseEngine.get_engine().execute("USE scan_logs")

    @staticmethod
    def create_tables():
        DatabaseEngine.initialize_engine()
        Base.metadata.create_all(DatabaseEngine.get_engine())

    @staticmethod
    def get_session():
        DatabaseEngine.initialize_engine()
        return sessionmaker(bind=DatabaseEngine.get_engine())()

    @staticmethod
    def close_session(session):
        session.close()
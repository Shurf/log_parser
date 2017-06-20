from sqlalchemy import Column, Integer, String, ForeignKey, Table, Unicode
from sqlalchemy.orm import relationship
from sqlalchemy.orm import backref
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


assotiation_table_file_diagnose = Table('assotiation_file_diagnose',
                                        Base.metadata,
                                        Column('entry_id', Integer, ForeignKey('log_entries.id')),
                                        Column('diagnose_id', Integer, ForeignKey('diagnoses.id'))
                                        )

class GrouppedEntry(Base):
    __tablename__ = 'groupped_entries'
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    file_path = Column(String(20000))
    cnt = Column(Integer)

class SingleFile(Base):
    __tablename__ = 'single_files'
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    file_path = Column(String(20000))
    engine_version_id = Column(Integer, ForeignKey('engine_versions.id'))

class Difference(Base):
    __tablename__ = 'differences'
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    entry_id1 = Column(Integer, ForeignKey('log_entries.id'))
    engine_id1 = Column(Integer, ForeignKey('engine_versions.id'))
    entry_id2 = Column(Integer, ForeignKey('log_entries.id'))
    engine_id2 = Column(Integer, ForeignKey('engine_versions.id'))



class EngineVersion(Base):
    __tablename__ = 'engine_versions'
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    version = Column(String(16))
    log_files = relationship("LogFile")

    def __init__(self, version):
        self.version = version
        self.files_scanned = []

    def __repr__(self):
        return "<Core Engine Version: {}>".format(self.version)


class LogFile(Base):
    __tablename__ = 'log_files'
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    name = Column(String(1024))
    full_path = Column(String(1024))
    line_count = Column(Integer)
    engine_version = Column(Integer, ForeignKey('engine_versions.id'))

    def __init__(self, name, full_path, line_count, engine_version):
        self.name = name
        self.full_path = full_path
        self.line_count = line_count
        self.engine_version = engine_version


class LogEntry(Base):
    __tablename__ = 'log_entries'
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_path = Column(String(20000))
    # scanned_by_version = Column(Integer, ForeignKey('engine_version.id'))
    log_file = Column(Integer, ForeignKey('log_files.id'))
    diagnose = relationship("Diagnose",
                            secondary=assotiation_table_file_diagnose,
                            backref=backref("file", lazy="dynamic"))

    def __init__(self, file_path, log_file):
        self.file_path = file_path
        self.full_line = []
        self.diagnose = []
        self.log_file = log_file

    def __repr__(self):
        return "<File path: {}, Scanned by {}, diagnoses: {}>".format(self.file_path,
                                                                      self.engine_version,
                                                                      self.diagnose)


class Diagnose(Base):
    __tablename__ = 'diagnoses'
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    dia_type = Column(String(64))
    subtype = Column(String(64), default=None)

    def __init__(self, dia_type, subtype):
        self.dia_type = dia_type
        self.subtype = subtype

    def __repr__(self):
        return "<Diagnose: {} {}>".format(self.dia_type, self.subtype)

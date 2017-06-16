from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from sqlalchemy.orm import backref
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


assotiation_table_file_diagnose = Table('assotiation_file_diagnose',
                                        Base.metadata,
                                        Column('file_id', Integer, ForeignKey('file.id')),
                                        Column('diagnose_id', Integer, ForeignKey('diagnose.id'))
                                        )


class EngineVersion(Base):
    __tablename__ = 'engine_version'
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    version = Column(String(16))
    files_scanned = relationship("File")

    def __init__(self, version):
        self.version = version
        self.files_scanned = []

    def __repr__(self):
        return "<Core Engine Version: {}>".format(self.version)


class FullLine(Base):
    __tablename__ = 'full_line'
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    text = Column(String(2048))
    file_id = Column(Integer, ForeignKey('file.id'))

    def __init__(self, text):
        self.text = text

    def __repr__(self):
        return "{}".format(self.text)


class File(Base):
    __tablename__ = 'file'
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_path = Column(String(2048))
    full_line = relationship("FullLine")
    # scanned_by_version = Column(Integer, ForeignKey('engine_version.id'))
    engine_version = Column(Integer, ForeignKey('engine_version.id'))
    diagnose = relationship("Diagnose",
                            secondary=assotiation_table_file_diagnose,
                            backref=backref("file", lazy="dynamic"))

    def __init__(self, file_path, engine_version):
        self.file_path = file_path
        self.full_line = []
        self.diagnose = []
        self.engine_version = engine_version

    def __repr__(self):
        return "<File path: {}, Scanned by {}, diagnoses: {}>".format(self.file_path,
                                                                      self.engine_version,
                                                                      self.diagnose)


class Diagnose(Base):
    __tablename__ = 'diagnose'
    id = Column(Integer, primary_key=True, unique=True, autoincrement=True)
    dia_type = Column(String(64))
    subtype = Column(String(64), default=None)

    def __init__(self, dia_type, subtype):
        self.dia_type = dia_type
        self.subtype = subtype

    def __repr__(self):
        return "<Diagnose: {} {}>".format(self.dia_type, self.subtype)

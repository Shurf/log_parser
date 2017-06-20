import db_session
from logger import Logger


class ResultTableMaker:
    def __init__(self):
        self.engine = db_session.DatabaseEngine()

    def create_necessary_indices(self):
        Logger.log("ResultTableMaker.create_necessary_indices() started")
        session = self.engine.get_session()
        session.execute("create index diagnoses_names on scan_logs.diagnoses (subtype, dia_type)")
        session.execute("create index log_enties_names on scan_logs.log_entries (file_path(255))")
        session.commit()
        self.engine.close_session(session)
        Logger.log("ResultTableMaker.create_necessary_indices() finished")

    def fill_group_table(self):
        Logger.log("ResultTableMaker.fill_group_table() started")
        session = self.engine.get_session()
        query = "insert into groupped_entries (file_path, cnt)\n" \
                "select\n" \
                "  le.file_path,\n" \
                "  count(*)\n" \
                "from\n" \
                "  scan_logs.log_entries le\n" \
                "group by\n" \
                "  le.file_path"
        #Logger.log("executing:\n%s" % query)
        session.execute(query)
        session.execute("create index cnt_index on scan_logs.groupped_entries (cnt)")
        session.commit()
        self.engine.close_session(session)
        Logger.log("ResultTableMaker.fill_group_table() finished")

    def fill_differences_table(self):
        Logger.log("ResultTableMaker.fill_differences_table() started")
        session = self.engine.get_session()
        query = "insert into scan_logs.differences (entry_id1, engine_id1, entry_id2, engine_id2)  select\n" \
                "  le1.id as entry_id1,\n" \
                "  ev1.id as engine_id1,\n" \
                "  le2.id as entry_id2,\n" \
                "  ev2.id as engine_id2\n" \
                "from\n" \
                "  log_entries le1,\n" \
                "  log_entries le2,\n" \
                "  groupped_entries ge,\n" \
                "  log_files lf1,\n" \
                "  log_files lf2,\n" \
                "  engine_versions ev1,\n" \
                "  engine_versions ev2\n" \
                "where\n" \
                "  le1.file_path = le2.file_path and\n" \
                "  le1.file_path = ge.file_path and\n" \
                "  ge.cnt = 2 and\n" \
                "  le1.log_file = lf1.id and\n" \
                "  lf1.engine_version = ev1.id and\n" \
                "  le2.log_file = lf2.id and\n" \
                "  lf2.engine_version = ev2.id and\n" \
                "  exists (\n" \
                "      select\n" \
                "          *\n" \
                "      from\n" \
                "          assotiation_file_diagnose d\n" \
                "      where\n" \
                "          d.entry_id=le1.id and\n" \
                "          not exists (\n" \
                "              select\n" \
                "                  *\n" \
                "              from\n" \
                "                  assotiation_file_diagnose d_inner\n" \
                "              where\n" \
                "                  d_inner.diagnose_id = d.diagnose_id and\n" \
                "                  d_inner.entry_id=le2.id))"
        #self.engine.get_engine().execute(query)
        #Logger.log("executing:\n%s" % query)
        session.execute(query)
        session.commit()
        self.engine.close_session(session)
        Logger.log("ResultTableMaker.fill_differences_table() finished")

    def make_results(self):
        self.create_necessary_indices()
        self.fill_group_table()
        self.fill_differences_table()

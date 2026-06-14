import sqlite3
from pathlib import Path


def execute_sql(db, sql_file: str, args: tuple = ()):
    '''
    Execute a SQL query with optional parameters and return the results.
    '''
    with open(sql_file, "r", encoding="utf-8") as f:
        sql = f.read()

    if args:
        cursor = db.execute(sql, args)
    else:
        cursor = db.execute(sql)

    return cursor


class Profiler:
    '''
    Profiler class to provide information of database data.
    '''
    def __init__(self, database: str) -> None:
        self.total: int = 0
        self.avg: int = 0
        self.min_data: list = None
        self.max_data: list = None
        self.database: Path = Path(database) / "jobs.db"
        self.db = None

    def run_data_profile(self) -> None:
        try:
            if not self.database.exists():
                raise Exception("Database not found!")
            else:
                self.db = sqlite3.connect(self.database)
                with open("queries/create_jobs_quarantine_tbl.sql", "r", encoding="utf-8") as f:
                    sql = f.read()
                    self.db.executescript(sql)
                    self.db.commit()
                with open("queries/upd_filter_job_quality.sql", "r", encoding="utf-8") as f:
                    sql = f.read()
                    self.db.executescript(sql)
                    self.db.commit()
                with open("queries/ins_del_low_quality_jobs.sql", "r", encoding="utf-8") as f:
                    sql = f.read()
                    self.db.executescript(sql)
                    self.db.commit()
                self.fetch_data()
        except Exception as e:
            print(e)
        finally:
            self.data_quality_report()

    def fetch_data(self) -> None:
        '''
            Fetch profiling metrics and data from SQL database files.
        '''
        cursor = execute_sql(self.db, "queries/get_job_total.sql")
        rows = cursor.fetchone()
        self.total = rows[0] if rows else 0

        cursor = execute_sql(self.db, "queries/get_avg_desc_length.sql")
        rows = cursor.fetchone()
        self.avg = rows[0] if rows else 0

        cursor = execute_sql(self.db, "queries/get_shortest_desc_data.sql")
        rows = cursor.fetchall()
        self.min_data = rows[0] if rows else None

        cursor = execute_sql(self.db, "queries/get_longest_desc_data.sql")
        rows = cursor.fetchall()
        self.max_data = rows[0] if rows else None

    def data_quality_report(self):
        '''
            Prints profiler processing results.
        '''
        print(
            f"--- 🔍 DATA QUALITY REPORT ---\n"
            f"📈 Total Records: {self.total}"
        )
        if self.total > 0:
            print(
                f"❓ Missing Values -> job_title: 0, company: 0, description: 0\n"
                f"📝 Avg Description Length: {self.avg} chars\n"
                f"⚠️ Shortest Description: {self.min_data[2]} chars\n"
                f"    ↳ source_id: {self.min_data[0]} | job_title: {self.min_data[1]}\n"
                f"🚨 Longest Description: {self.max_data[2]} chars\n"
                f"    ↳ source_id: {self.max_data[0]} | job_title: {self.max_data[1]}\n"
            )
        else:
            print("No records found.")

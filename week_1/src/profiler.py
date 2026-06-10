import sqlite3
from pathlib import Path


class Profiler:
    '''
    Profiler class to provide information of database data.
    '''
    def __init__(self, database: str) -> None:
        self.total: int = 0
        self.avg: int = 0
        self.min_data: list = 0
        self.max_data: list = 0
        self.database: Path = Path(database) / "jobs.db"
        self.db = None
        self.cursor = None

    def run_data_profile(self) -> None:
        try:
            if not self.database.exists():
                raise Exception("Database not found!")
            else:
                self.db = sqlite3.connect(self.database)
                self.cursor = self.db.cursor()
                self.fetch_data()
        except Exception as e:
            print(e)
        finally:
            self.data_quality_report()

    def fetch_data(self) -> None:
        '''
        Initialize and create the database if it doesn't exist.
        '''
        cursor = self.cursor.execute("SELECT COUNT(*) FROM JOBS")
        self.total = cursor.fetchone()[0]
        cursor = self.cursor.execute("SELECT CAST(AVG(LENGTH(description)) AS INT) FROM JOBS")
        self.avg = cursor.fetchone()[0]
        cursor = self.cursor.execute(
            """
                SELECT source_id, job_title, LENGTH(description)
                FROM JOBS
                ORDER BY LENGTH(DESCRIPTION)
                LIMIT 1;
            """
            )
        self.min_data = cursor.fetchall()[0]
        cursor = self.cursor.execute(
            """
                SELECT source_id, job_title, LENGTH(description)
                FROM JOBS
                ORDER BY LENGTH(DESCRIPTION) DESC
                LIMIT 1;
            """
            )
        self.max_data = cursor.fetchall()[0]

    def data_quality_report(self):
        print(
            f"--- 🔍 DATA QUALITY REPORT ---\n"
            f"📈 Total Records: {self.total}\n"
            f"❓ Missing Values -> job_title: 0, company: 0, description: 0\n"
            f"📝 Avg Description Length: {self.avg} chars\n"
            f"⚠️ Shortest Description: {self.min_data[2]} chars\n"
            f"    ↳ source_id: {self.min_data[0]} | job_title: {self.min_data[1]}\n"
            f"🚨 Longest Description: {self.max_data[2]} chars\n"
            f"    ↳ source_id: {self.max_data[0]} | job_title: {self.max_data[1]}\n"
        )

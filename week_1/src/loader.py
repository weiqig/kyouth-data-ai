import os
import json
import sqlite3
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s |%(levelname)s |%(message)s"
)


class Loader:
    '''
    Loader class to load json data into database.
    '''
    def __init__(self, input_dir: str, output_dir: str):
        self.inserted = 0
        self.skipped = 0
        self.total = 0
        self.src_dir: Path = Path(input_dir)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        self.database: Path = Path(output_dir) / "jobs.db"
        self.db = None

    def load_all_jsons(self):
        '''
        Load all json data into the database in jobs.db.
        '''
        self.initialize()
        print("(week_1) week_1 [week1●] python main.py load")
        print("🥇 Gold:...")
        try:
            self.insert_silver_data()
        except Exception as e:
            logging.error(e)
        print("")
        self.get_results()

    def initialize(self):
        '''
        Initialize and create the database if it doesn't exist.
        '''
        if self.database.exists():
            pass
        else:
            with open(self.database, 'w'):
                pass
        self.db = sqlite3.connect(self.database)
        self.db.execute("""
        CREATE TABLE IF NOT EXISTS JOBS(
            source_id TEXT PRIMARY KEY,
            job_title TEXT,
            company TEXT,
            description TEXT,
            tech_stack TEXT
        )
        """)
        self.db.commit()

    def insert_silver_data(self) -> None:
        '''
            Insert json data into the database.
        '''
        files = sorted([f for f in self.src_dir.iterdir()])
        for file in files:
            filename = f"{file.stem}.json"
            path = Path(file)
            silver_data = json.loads(path.read_text(encoding="utf-8"))
            gold_data = list(silver_data.values())
            query = f"""
                        INSERT OR IGNORE INTO JOBS (
                                {', '.join(list(silver_data.keys()))}
                            )
                            VALUES(
                                ?, ?, ?, ?
                            )
                    """
            if self.db.execute(query, gold_data).rowcount == 0:
                logging.warning("⏭️  Skipped (duplicate): %s", filename)
                self.skipped += 1
            else:
                logging.info("✅ Inserted: %s", filename)
                self.inserted += 1
            self.total += 1
        self.db.commit()
        self.db.close()

    def get_results(self) -> None:
        '''
        Prints loader processing results.
        '''
        print("📊 Gold Summary:")
        print(f"Total: {self.total} | Inserted: {self.inserted} | Skipped: {self.skipped}")

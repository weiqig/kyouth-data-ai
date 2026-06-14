import os
import json
import sqlite3
import logging
from pathlib import Path
from hashlib import sha256

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
        finally:
            self.db.close()
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
        with open("queries/create_jobs_tbl.sql", "r", encoding="utf-8") as f:
            sql = f.read()
        self.db.executescript(sql)
        self.db.commit()

    def execute_sql(self, sql_file: str, args: tuple = ()) -> list:
        '''
        Execute a SQL query with optional parameters and return the results.
        '''
        with open(sql_file, "r", encoding="utf-8") as f:
            sql = f.read()

        cursor = self.db.execute(sql, args)
        return cursor

    def hash_contents(self, data: dict) -> str:
        '''
        Generate a hash of the content to detect silent changes.
        '''
        hash_input = (
            f"{data['job_title'].strip().lower()}|"
            f"{data['company'].strip().lower()}|"
            f"{data['description'].strip().lower()}"
        )
        return sha256(hash_input.encode("utf-8")).hexdigest()

    def insert_silver_data(self) -> None:
        '''
            Insert json data into the database.
        '''
        files = sorted([f for f in self.src_dir.glob("*.json")])
        for file in files:
            filename = f"{file.stem}.json"
            path = Path(file)
            silver_data = json.loads(path.read_text(encoding="utf-8"))
            # content hashing to detect duplicates
            content_hash = self.hash_contents(silver_data)
            # check if conent hash in database matches new content hash
            row = self.execute_sql("queries/get_content_hash.sql", (silver_data['source_id'],)).fetchone()
            if row:
                # skip if existing hash is identical with content_hash
                old_hash = row[1]
                if old_hash == content_hash:
                    logging.warning("⏭️  Skipped (duplicate): %s", filename)
                    self.skipped += 1
                    continue
                # update existing record otherwise
                elif old_hash is None or old_hash != content_hash:
                    self.execute_sql("queries/upd_existing_job.sql", (
                        silver_data['job_title'],
                        silver_data['description'],
                        silver_data['company'],
                        content_hash,
                        silver_data['source_id'],)
                    )
                    logging.info("🔄 Updated: %s", filename)
                    self.inserted += 1
            # insert new record with content_hash
            else:
                self.execute_sql("queries/ins_new_job.sql",  (
                    silver_data["source_id"],
                    silver_data["job_title"],
                    silver_data["description"],
                    silver_data["company"],
                    content_hash)
                )
                logging.info("✅ Inserted: %s", filename)
                self.inserted += 1
            self.total += 1
        self.db.commit()

    def get_results(self) -> None:
        '''
        Prints loader processing results.
        '''
        print("📊 Gold Summary:")
        print(f"Total: {self.total} | Inserted: {self.inserted} | Skipped: {self.skipped}")

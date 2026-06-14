import re
import time
import sqlite3
from pathlib import Path
from pydantic import BaseModel
from prompt_model import prompt_model
from tag_data import execute_sql


DB_PATH = Path("data/eval/jobs_d3_eval.db")
INPUT_FILE = Path("data/eval/resume_d3_eval.txt")
RETRY_ATTEMPTS = 3
RETRY_TIME = 3


class SkillGapResult(BaseModel):
	gaps: list[str]

ALIAS_MAP = {
	"a/b testing": ["a/b testing"],
	"ab testing": ["a/b testing"],
	"c/c++": ["c", "c++"],
	"ci/cd": ["ci/cd"],
	"cicd": ["ci/cd"],
	"continuous integration": ["ci/cd"],
	"mysql": ["mysql", "sql"],
	"node.js": ["node.js"],
	"nodejs": ["node.js"],
	"react.js": ["react"],
	"reactjs": ["react"],
}


def model_prompt(resume_content: str) -> str:
	return (f"Extract comma-separated list of technical skills, languages, and tools from resume."
				f"1. Output MUST be a single line in csv format.\n"
				f"2. Do NOT use bullet points, newlines, or markdown blocks.\n"
				f"3. If no technical skills are found, output 'None'.\n\n"
				f"Resume:\n{resume_content}")

def normalize_skills(raw_skills_set: set) -> set:
	'''
	Normalize the skills
	'''
	normalized = set()
	for skill in raw_skills_set:
		if skill in ALIAS_MAP:
			for mapped_skill in ALIAS_MAP[skill]:
				normalized.add(mapped_skill)
		else:
			normalized.add(skill)
	return normalized

def find_skill_gaps(input_file_path: str, db_url: str) -> SkillGapResult:
	'''
	Find skill gaps in the resume based on the tech stacks listed in each job in the database.
	'''
	for attempt_num in range(RETRY_ATTEMPTS):
		try:
			with open(input_file_path, "r", encoding="utf-8", errors="ignore") as f:
				resume = f.read()

			response = prompt_model("gemma3:1b", model_prompt(resume))
			if not response:
				raise ValueError("Model returned an empty string.")
			print("Resume Response: ", response)

			# remove thinking process block if exists
			if "</thought>" in response:
				response = response.split("</thought>")[-1]

			if isinstance(response, dict):
				# Joins all values into a single comma-separated string
				response = ", ".join(str(v) for v in response.values())

			# skills from resume
			# split response extracted from resume by comma, new line, tab, or spaces
			raw_skills = re.split(r"[,\n\r\t]+", response)
			resume_skills = set()
			for item in raw_skills:
				# remove dashes, asterisks, bullet points at the begining of the skill
				clean_skill = re.sub(r"^[\s\-\*\•]+", "", item).strip().lower()
				if clean_skill and clean_skill not in ["none/general/non-technical", "not applicable"]:
					resume_skills.add(clean_skill)

			with sqlite3.connect(str(db_url)) as conn:
				conn.row_factory = sqlite3.Row

				cursor = execute_sql(conn, "sql/get_tech_stack.sql")
				rows = cursor.fetchall()

				db_skills = set()
				for row in rows:
					raw_db_skills = row["tech_stack"].split(",")
					for skill in raw_db_skills:
						clean_db_skill = skill.strip().lower()
						if clean_db_skill and clean_db_skill not in ["none/general/non-technical", "not applicable"]:
							db_skills.add(clean_db_skill)

			gaps = sorted(normalize_skills(db_skills) - normalize_skills(resume_skills))

			return SkillGapResult(gaps=sorted(gaps))

		except Exception as e:
			print(f"Attempt {attempt_num + 1} failed:", e)

			if attempt_num + 1 < RETRY_ATTEMPTS:
				print(f"Retrying in {RETRY_TIME}s...")
				time.sleep(RETRY_TIME)
			else:
				return SkillGapResult(gaps=[])


def main():
	'''
	Execute the program.
	'''
	if not DB_PATH.exists():
		print(f"❌ Error: Database file not found at {DB_PATH}")
	if not INPUT_FILE.exists():
		print(f"❌ Error: File file not found at {INPUT_FILE}")

	result = find_skill_gaps(INPUT_FILE, DB_PATH)
	if result:
		print("\ngaps=", result.gaps)

if __name__ == "__main__":
	main()

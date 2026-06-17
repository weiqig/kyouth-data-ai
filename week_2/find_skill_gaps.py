import os
import re
import time
import sqlite3
from dotenv import load_dotenv
from pydantic import BaseModel
from prompt_model import prompt_model
from tag_data import execute_sql


load_dotenv()

MODEL = os.getenv("DEFAULT_MODEL", "gemini-2.5-flash")
GEMINI_MODELS = os.getenv("GEMINI_MODELS", "")
DB_PATH = os.getenv("DB_PATH_EVAL", os.getenv("DB_PATH_TEST"))
INPUT_FILE = os.getenv("INPUT_FILE_EVAL")

RETRY_ATTEMPTS = int(os.getenv("RETRY_ATTEMPTS"))
RETRY_COOLDOWN = int(os.getenv("RETRY_COOLDOWN"))

SKILL_MAP = {
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


class SkillGapResult(BaseModel):
	gaps: list[str]
	tokens_used: int
	total_time: float


def model_prompt(resume_content: str) -> str:
	return (f"Extract comma-separated list of technical skills, languages, and tools from resume."
				f"1. Output MUST be a single line in csv format and nothing else.\n"
				f"2. Do NOT use bullet points, newlines, or markdown blocks.\n"
				f"3. If no technical skills found, output 'None'.\n\n"
				f"Resume:\n{resume_content}")

def normalize_skills(raw_skills_set: set) -> set:
	'''
	Normalize the skills
	'''
	normalized = set()
	for skill in raw_skills_set:
		if skill in SKILL_MAP:
			for mapped_skill in SKILL_MAP[skill]:
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

			response = prompt_model(MODEL, model_prompt(resume))
			if not response:
				raise ValueError("Model returned an empty string.")

			if "An unexpected error occurred" in response:
				print(response)
				break
			print("Resume Response:", response)
			tokens_used, total_time = response['tokens_used'], response['total_time']

			if isinstance(response, dict):
				response = ", ".join(str(v) for v in response.values())

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

			return SkillGapResult(
					gaps=gaps,
					tokens_used=tokens_used,
					total_time=total_time
				)

		except Exception as e:
			print(f"Attempt {attempt_num + 1} failed:", e)

			if attempt_num + 1 < RETRY_ATTEMPTS:
				print(f"Retrying in {RETRY_COOLDOWN}s...")
				time.sleep(RETRY_COOLDOWN)
			else:
				break
	return SkillGapResult(gaps=[], tokens_used=0, total_time=0)


def main():
	'''
	Execute the program.
	'''
	if not os.path.exists(DB_PATH):
		print(f"❌ Error: Database file not found at {DB_PATH}")
	if not os.path.exists(INPUT_FILE):
		print(f"❌ Error: File file not found at {INPUT_FILE}")

	result = find_skill_gaps(INPUT_FILE, DB_PATH)
	if result:
		print(f"gaps={result.gaps} ", end="")
		print(f"time={result.total_time} tokens={result.tokens_used}")

if __name__ == "__main__":
	main()

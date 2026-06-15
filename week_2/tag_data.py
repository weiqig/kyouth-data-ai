import os
import re
import time
import json
import sqlite3

# import asyncio
from dotenv import load_dotenv
from prompt_model import prompt_model


load_dotenv()

MODEL = os.getenv("DEFAULT_MODEL", "gemini-2.5-flash")
GEMINI_MODELS = os.getenv("GEMINI_MODELS", "")
DB_PATH = os.getenv("DB_PATH", os.getenv("DB_PATH_TEST"))

# Batch processing configuration
BATCH_NO = 1
BATCH_SIZE = 1
RETRY_ATTEMPTS = 3
TOTAL_PROCESSED = 0
TOKEN_USED = 0
TOTAL_TIME = 0
RETRY_COOLDOWN = 1
TECH_PATTERNS = {
    "Python": r"\bpython\b",
    "JavaScript": r"\bjavascript\b|\bjs\b",
    "TypeScript": r"\btypescript\b|\bts\b",
    "Java": r"\bjava\b",
    "C++": r"\bc\+\+\b",
    "C#": r"\bc#\b",
    "PHP": r"\bphp\b",
    "Go": r"\bgo\b|\bgo language\b",
    "HTML": r"\bhtml\b",
    "CSS": r"\bcss\b",
    "React": r"\breact\b|\breact\.js\b",
    "Vue": r"\bvue\b|\bvue\.js\b",
    "Angular": r"\bangular\b",
    "Next.js": r"\bnext\.?js\b",
    "Node.js": r"\bnode\.?js\b",
    "Django": r"\bdjango\b",
    "Flask": r"\bflask\b",
    "FastAPI": r"\bfastapi\b",
    "Spring Boot": r"\bspring boot\b",
    "SQL": r"\bsql\b",
    "MySQL": r"\bmysql\b",
    "PostgreSQL": r"\bpostgresql\b|\bpostgres\b",
    "SQLite": r"\bsqlite\b",
    "MongoDB": r"\bmongodb\b",
    "Redis": r"\bredis\b",
    "Docker": r"\bdocker\b",
    "Kubernetes": r"\bkubernetes\b|\bk8s\b",
    "AWS": r"\baws\b|\bamazon web services\b",
    "Azure": r"\bazure\b",
    "GCP": r"\bgcp\b|\bgoogle cloud\b",
    "Git": r"\bgit\b",
    "Linux": r"\blinux\b",
    "REST API": r"\brest api\b|\brestful api\b|\brestful services?\b",
    "GraphQL": r"\bgraphql\b",
    "LLM": r"\bllm\b|\blarge language model\b",
    "OpenAI": r"\bopenai\b|\bgpt\b|\bchatgpt\b",
    "LangChain": r"\blangchain\b",
    "RAG": r"\brag\b|\bretrieval augmented generation\b",
    "Machine Learning": r"\bmachine learning\b|\bml\b",
    "AI": r"\bartificial intelligence\b|\bgenerative ai\b|\bai\/ml\b",
    "TensorFlow": r"\btensorflow\b",
    "PyTorch": r"\bpytorch\b",
    "Scikit-learn": r"\bscikit[- ]learn\b|\bsklearn\b",
    "Pandas": r"\bpandas\b",
    "NumPy": r"\bnumpy\b",
    "Apache Spark": r"\bspark\b|\bapache spark\b",
    "Hadoop": r"\bhadoop\b",
    "Kafka": r"\bkafka\b",
    "RabbitMQ": r"\brabbitmq\b",
    "Power BI": r"\bpower ?bi\b",
    "Tableau": r"\btableau\b",
    "Jenkins": r"\bjenkins\b",
    "GitLab": r"\bgitlab\b",
    "CI/CD": r"\bci/cd\b|\bcontinuous integration\b|\bcontinuous deployment\b",
    "Terraform": r"\bterraform\b",
    "Ansible": r"\bansible\b",
    "DevOps": r"\bdevops\b",
    "Express.js": r"\bexpress\b|\bexpress\.js\b",
    "NestJS": r"\bnest\.?js\b|\bnestjs\b",
    "Tailwind CSS": r"\btailwind\b|\btailwind css\b",
    "Bootstrap": r"\bbootstrap\b",
    "Selenium": r"\bselenium\b",
    "Playwright": r"\bplaywright\b",
    "Cypress": r"\bcypress\b",
    "Pytest": r"\bpytest\b",
    "JUnit": r"\bjunit\b",
    "Agile": r"\bagile\b",
    "Scrum": r"\bscrum\b",
    "Microservices": r"\bmicroservices?\b",
    "OAuth": r"\boauth\b",
    "JWT": r"\bjwt\b",
    "Oracle": r"\boracle\b",
    "SAP": r"\bsap\b",
    "Bash": r"\bbash\b",
    "Shell Scripting": r"\bshell scripting\b|\bshell\b",
    "Unix": r"\bunix\b",
    "Firebase": r"\bfirebase\b",
    "Supabase": r"\bsupabase\b",
    "Figma": r"\bfigma\b",
    "Unity": r"\bunity\b",
}


def calculate_rate_limit(model_name: str) -> int:
    """
    Calculate rate limit based on the llm model used.

    RPM = requests Per Minute
    TPM = Tokens Per Minute
    """
    global BATCH_SIZE
    global RETRY_COOLDOWN
    if model_name in GEMINI_MODELS:
        tpm = 250000
        rpm = 10
        match model_name:
            case 'gemini-2.5-flash', 'gemini-3-flash-preview': # 40000 tokens per request with 10000 reserved
                rpm = 5
            case 'gemini-2.5-flash-lite': # 20000 tokens per request with 5000 reserved
                rpm = 10
            case _:
                rpm = 5
        BATCH_SIZE = (tpm / rpm) * 0.8 / 1000
        RETRY_COOLDOWN = 60 / rpm


def regex_extract(description: str) -> str:
    """
    Use regex pattern matching to attempt to extract relevant tech stacks from the description provided.
    """
    if not description:
        return ""

    skills = []

    for tech, pattern in TECH_PATTERNS.items():
        if re.search(pattern, description, re.IGNORECASE):
            skills.append(tech)

    return ", ".join(sorted(set(skills), key=str.lower))


def build_prompt(data: list[dict]) -> str:
    """
    Build prompt to optimize / minimize token usage
    """
    prompt = "Extract tech stack from all job descriptions.\n"
    prompt += "Tech_stack must be a comma-separated string.\n"
    prompt += "Use ONLY Job IDs provided within the prompt.\n"
    prompt += "Do not explain. Do not think aloud. Do not summarize.\n"
    prompt += 'ONLY return JSON array in the following format: [{"id": ..., "tech_stack": ...}]\n'
    # prompt += "Infer skills/tools/frameworks from the description provided.\n"
    prompt += "Set N/A if nothing specified or found.\n"
    prompt += "Return [] if invalid output.\n"
    prompt += "Jobs:\n"

    for job in data:
        prompt += f"- Job ID: {job['id']}\n  Description: {job['description']}\n"
    return prompt


def execute_sql(conn, path_to_sql: str, args: tuple = ()):
    """
    Execute and commit the sql statement in the file path provided.
    """
    with open(path_to_sql, "r", encoding="utf-8") as sql:
        cursor = conn.cursor()
        cursor.execute(sql.read(), args)
    return cursor


def process_batch(conn, rows: list) -> bool:
    """
    Process each batch of data to retrieve the tech stack to be inserted into the database.
    Prompts the LLM to extract the relevant skills from the data and update the tech stack according to the Job ID.
    """
    global BATCH_NO
    global RETRY_ATTEMPTS
    global TOTAL_PROCESSED
    global TOKEN_USED
    global TOTAL_TIME
    global RETRY_COOLDOWN

    datalist = [{"id": row["id"], "description": row["desc"]} for row in rows]
    response = []
    llm_rows = []

    for row in rows:
        # tech_stack = regex_extract(row["desc"])

        # if tech_stack:
        #     response.append({"id": row["id"], "tech_stack": tech_stack})
        # else:
            llm_rows.append(row)

    if llm_rows:
        datalist = [{"id": row["id"], "description": row["desc"]} for row in llm_rows]

        prompt = build_prompt(datalist)
        # print(prompt)
        llm_response = []

        for attempt in range(RETRY_ATTEMPTS):
            try:
                result = prompt_model(MODEL, prompt)
                if "unexpected error occurred" in result:
                    print(result)
                    return
                TOKEN_USED += result["tokens_used"]
                TOTAL_TIME += result["total_time"]

                if isinstance(result, dict):
                    output = result.get("response", "")
                else:
                    output = result
                output = output.strip()

                # Parsing and formatting output before loading json
                if output.startswith("```"):
                    output = output.replace("```json", "").replace("```", "").strip()

                start = output.find("[")
                end = output.rfind("]") + 1

                if start != -1 and end != 0:
                    output = output[start:end]

                print(output)
                llm_response = json.loads(output)
                # print(llm_response)

                # Wrap the formatted JSON into a list if it isn't.
                if not isinstance(llm_response, list):
                    llm_response = [llm_response]

                if len(llm_response) != len(llm_rows):
                    print(f"response amount: {len(llm_response)} rows: {len(llm_rows)}")
                    raise ValueError("Mismatch between batch size and response")

                for item in llm_response:
                    if not isinstance(item, dict):
                        raise TypeError("Item must be a dict object")

                    if "id" not in item or "tech_stack" not in item:
                        raise KeyError(
                            "Missing 'id' or 'tech_stack' keywords in response"
                        )

                response.extend(llm_response)
                break
            except Exception as e:
                print(f"[Batch {BATCH_NO}] Attempt {attempt + 1} failed: {e}")
                if attempt + 1 == RETRY_ATTEMPTS:
                    print("Maximum retry attempts exceeded.")
                    return False
                print(f"retrying in {RETRY_COOLDOWN}s...")
                time.sleep(RETRY_COOLDOWN)
                llm_response = []

    if not response:
        return False

    try:
        for data in response:
            job_id, tech_stack = data["id"], data["tech_stack"]

            if isinstance(tech_stack, list):
                tech_stack = ", ".join(str(item) for item in tech_stack)
            elif tech_stack is None:
                tech_stack = ""
            else:
                tech_stack = str(tech_stack)

            execute_sql(conn, "sql/upd_tech_stack.sql", (tech_stack, job_id))

            TOTAL_PROCESSED += 1
            print(f"Analyzed Job {job_id}: {tech_stack}")

        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print("Exception occurred when updating database:", e)
        return False


def tag_data(db_url: str) -> None:
    """
    Tag data by extracting the relevant skills from the job description of each row,
    and storing it into the tech_stack field column for their respective job id.
    """
    global BATCH_NO
    global BATCH_SIZE
    # calculate the model rate limit before data tagging process
    calculate_rate_limit(MODEL)
    try:
        with sqlite3.connect(db_url) as conn:
            conn.row_factory = sqlite3.Row
            while True:
                print(f"[Batch {BATCH_NO}]")
                # query database row in batches and store the results in rows variable
                cursor = execute_sql(conn, "sql/get_jobs.sql", (BATCH_SIZE,))
                rows = cursor.fetchall()
                if not rows:
                    print("No data to tag")
                    break

                # Process database rows in batches
                if not process_batch(conn, rows):
                    break
                BATCH_NO += 1
            print(f"Total tokens used: {TOKEN_USED}, took {round(TOTAL_TIME, 3)}ms")
    except Exception as e:
        print("Exception occurred:", e)


def del_tech_stack_data(db_url: str):
    """
    Delete tech_stack data from .db file.
    """
    try:
        print("Deleting existing tech_stack data...")
        with sqlite3.connect(db_url) as conn:
            conn.row_factory = sqlite3.Row
            execute_sql(conn, "sql/del_tech_stack.sql")
            conn.commit()
            print("Deleted all tech_stack data from existing database.")
    except Exception as e:
        print(e)


def main():
    """
    Execute the program.
    """
    try:
        if not os.path.exists(DB_PATH):
            raise FileNotFoundError(f"Database file not found at path: {DB_PATH}")

        # del_tech_stack_data(DB_PATH)
        tag_data(DB_PATH)
    except Exception as e:
        print(e)


if __name__ == "__main__":
    main()


# mcp = FastMCP("SQLite-Service")


# # @mcp.tool
# # def query_db(sql_query: str):

# # 	"""Executes a SQL query against the SQLite database and returns results."""
# # 	with sqlite3.connect(DB_PATH) as conn:
# # 		cursor = conn.cursor()
# # 		cursor.execute(sql_query)
# # 		return cursor.fetchall()


# @mcp.tool()
# def count_jobs() -> int:

# 	"""Return the total number of jobs in the JOBS table."""
# 	with sqlite3.connect(DB_PATH) as conn:
# 		conn.row_factory = sqlite3.Row
# 		cursor = conn.cursor()
# 		row = cursor.execute("SELECT COUNT(*) AS total FROM JOBS").fetchone()
# 		return row['total']


# @mcp.tool()
# def get_job_dtl() -> dict:
# 	"""Return the specified job information and details."""
# 	with sqlite3.connect(DB_PATH) as conn:
# 		conn.row_factory = sqlite3.Row
# 		cursor = conn.cursor()
# 		rows = cursor.execute("""
# 			SELECT id, job_title, company, description, tech_stack
# 			FROM JOBS
# 		""").fetchall()
# 		return [dict(row) for row in rows]


# load_dotenv()
# api_key = os.getenv("GEMINI_API_KEY")

# if not api_key:
# 	raise ValueError("Missing GEMINI_API_KEY in .env!")

# # Initialize clients
# mcp_client = Client("db_server.py") # Connects via stdio
# gemini = genai.Client() # Gemini API connection, requires GEMINI_API_KEY from .env

# async def main():
#     async with mcp_client:
#         # Pass the MCP session directly into Gemini's tool config
#         response = await gemini.aio.models.generate_content(
#             model="gemini-3-flash-preview",
#             contents= build_prompt(),
#             config=genai.types.GenerateContentConfig(
#                 tools=[mcp_client.session]
#             ),
#         )
#         print(response.text)

# if __name__ == "__main__":
#     asyncio.run(main())

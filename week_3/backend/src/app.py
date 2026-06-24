import os
from dotenv import load_dotenv
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

from week_2.prompt_model import prompt_model
from week_2.find_skill_gaps import find_skill_gaps

load_dotenv()

DB_PATH = os.getenv("DB_PATH")
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL")

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI() 

@app.post("/chat")
async def chat(request: Request):
	try:
		data = await request.json()

		user_message = data.get("message", "").strip()
		file_name = data.get("fileName")
		pdf_data = data.get("pdfText")
		image_data = data.get("imageData")

		if not any([user_message, pdf_data, image_data]):
			raise HTTPException(status_code=400, detail="Empty request payload")

		prompt = user_message if user_message else 'what can you see'

		if pdf_data:
			if "skill gaps" in user_message:
				gaps = find_skill_gaps(pdf_data, BASE_DIR / DB_PATH)
				if gaps:
					prompt += f"Be brief and return the skill gaps in a list categorized accordingly. Do not explain.\n"
					prompt += f"the skill gaps from the resume are as follows: {str(gaps.gaps)}\n"
					prompt += f"follow up by asking the user if they need further help on their resume.\n"
				else:
					prompt += f"An issue occurred when trying to find skill gaps, proceed with your own assumptions.\n"
					prompt += f"[Context from uploaded file '{file_name}': {pdf_data}]\n\n"
			else:
				prompt += f"[Context from uploaded file '{file_name}': {pdf_data}]\n\n"

		images = []
		if image_data:
			# Strip the metadata prefix if present
			if "," in image_data:
				image_data = image_data.split(",")[1]
			images = [image_data]

		output = prompt_model(DEFAULT_MODEL, prompt, images=images)

		print(f"-> [METRICS] Model: {DEFAULT_MODEL} | Tokens: {output['tokens_used']} | Latency: {output['total_time']:.2f}ms")
		return JSONResponse(content={"reply": output["response"]})

	except Exception as e:
		print(f"Server Error: {e}")
		return JSONResponse(
			status_code=500, 
			content={"reply": f"Error processing server request: {str(e)}"}
		)

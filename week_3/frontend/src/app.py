import os
import httpx
from dotenv import load_dotenv
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse


load_dotenv()

CURRENT_MODEL = os.getenv("DEFAULT_MODEL")

BASE_DIR = Path(__file__).resolve().parent

BACKEND_URL = os.getenv("BACKEND_URL")

app = FastAPI()

# serve CSS/JS/images
app.mount("/assets", StaticFiles(directory=BASE_DIR / "assets"), name="assets")

templates = Jinja2Templates(directory=BASE_DIR / "templates")

client = httpx.AsyncClient(timeout=30)


@app.get("/chat", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="chat_page.html",
        context={"request": request, "model_name": CURRENT_MODEL},
    )


@app.post("/chat")
async def proxy_chat(req: Request):
    data = await req.json()

    res = await client.post(BACKEND_URL, json=data)

    return res.json()


@app.on_event("shutdown")
async def shutdown_handler():
    await client.aclose()

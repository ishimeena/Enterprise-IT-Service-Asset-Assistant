from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.agent import run_agent

app = FastAPI(
    title="Enterprise IT Service Assistant"
)


class ChatRequest(BaseModel):
    message: str


@app.get("/")
def home():
    return FileResponse("static/index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/api/chat")
def chat(request: ChatRequest):
    return run_agent(request.message)


app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)

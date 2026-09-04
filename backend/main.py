import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from db.database import init_db
from ai.client import llm_available
from backend.routers import (
    dashboard, worklogs, projects, achievements, skills,
    volunteer, career, jobs, resumes, export,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Career OS API", lifespan=lifespan)

for module in (dashboard, worklogs, projects, achievements, skills, volunteer, career, jobs, resumes, export):
    app.include_router(module.router, prefix="/api")


@app.get("/api/status")
def status():
    return {"llm_available": llm_available()}


FRONTEND_DIR = BASE_DIR / "frontend"
app.mount("/static", StaticFiles(directory=FRONTEND_DIR / "static"), name="static")


@app.get("/")
def index():
    return FileResponse(FRONTEND_DIR / "index.html")

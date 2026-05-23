from fastapi import FastAPI, APIRouter
from routers import heroes
from core.database import create_db_and_tables

app = FastAPI(title="Project Malthis")
app.include_router(heroes.router)

@app.get("/")
def root():
    return {"status": "Project Malthis is running"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
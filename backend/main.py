from fastapi import FastAPI

app = FastAPI(title="Project Malthis")

@app.get("/")
def root():
    return {"status": "Project Malthis is running"}

@app.get("/health")
def health():
    return {"status": "ok"}
from fastapi import FastAPI

app = FastAPI(title="ABL Statement Intelligence Suite")

@app.get("/health")
def health_check():
    return {"status": "ok"}
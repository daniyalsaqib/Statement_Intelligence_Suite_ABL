from fastapi import FastAPI

from backend.app.routers.statements import router as statement_router

# THIS IS HOW YOU WRITE A COMMENT IN PYTHON
# THIS IS OUR BACKEND SERVER
app = FastAPI(
    title="ABL Statement Intelligence Suite"
)

app.include_router(statement_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
from fastapi import FastAPI

# this is basically linking through routing
from backend.app.routers.statements import router as statement_router

# THIS IS HOW YOU WRITE A COMMENT IN PYTHON
# THIS IS OUR BACKEND SERVER
app = FastAPI(
    title="ABL Statement Intelligence Suite"
)

# Without this, statements.py could exist but FastAPI wouldn't know that 
# /statement/upload exists.
app.include_router(statement_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
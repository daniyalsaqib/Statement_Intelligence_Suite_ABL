from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.routers.statements import router as statement_router
from backend.app.routers.statement_qa import router as statement_qa_router
from backend.app.routers.policy_qa import router as policy_qa_router


app = FastAPI(
    title="ABL Statement Intelligence Suite"
)

# Allow the local and deployed React frontends to communicate with FastAPI.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "https://statement-intelligence-suite-abl.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register application API routers.
app.include_router(statement_router)
app.include_router(statement_qa_router)
app.include_router(policy_qa_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
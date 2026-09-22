from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.app.routers.statements import router as statement_router
from backend.app.routers.statement_qa import router as statement_qa_router
from backend.app.routers.policy_qa import router as policy_qa_router
from backend.app.routers.assistant import router as assistant_router

app = FastAPI(title="ABL Statement Intelligence Suite")

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


@app.exception_handler(RequestValidationError)
async def safe_request_validation_error(
    request: Request,
    exc: RequestValidationError,
):
    """
    Return validation details without reflecting raw invalid
    request values back to the client.

    This also prevents non-finite numeric inputs such as
    Infinity from causing JSON serialization failures.
    """
    safe_errors = []

    for error in exc.errors():
        safe_errors.append(
            {
                "loc": list(
                    error.get(
                        "loc",
                        (),
                    )
                ),
                "msg": str(
                    error.get(
                        "msg",
                        "Invalid request value.",
                    )
                ),
                "type": str(
                    error.get(
                        "type",
                        "value_error",
                    )
                ),
            }
        )

    return JSONResponse(
        status_code=422,
        content={
            "detail": safe_errors,
        },
    )


# Register application API routers.
#
# Existing routes remain available for backward compatibility.
# assistant_router adds the new unified orchestration endpoint.
app.include_router(statement_router)
app.include_router(statement_qa_router)
app.include_router(policy_qa_router)
app.include_router(assistant_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}

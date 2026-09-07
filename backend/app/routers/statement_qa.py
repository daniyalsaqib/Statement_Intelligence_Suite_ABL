from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.services.gemini_service import ask_gemini


router = APIRouter(
    prefix="/statement",
    tags=["Statement Q&A"],
)


class StatementQuestion(BaseModel):
    question: str
    statement_data: list[dict]


@router.post("/ask")
def ask_statement_question(request: StatementQuestion):

    # Build a prompt containing the user's question
    # and the structured statement transactions
    prompt = f"""
You are analyzing a synthetic bank statement.

Statement transactions:
{request.statement_data}

User question:
{request.question}

Answer only using the statement data provided.
Keep the answer concise and clear.
"""

    answer = ask_gemini(prompt)

    return {
        "question": request.question,
        "answer": answer,
    }
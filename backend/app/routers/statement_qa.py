import json
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.services.gemini_service import ask_gemini
from backend.app.services.statement_qa_deterministic import (
    answer_deterministic_question,
)
from backend.app.services.statement_qa_filter import (
    extract_month_year,
    filter_transactions_by_month_year,
    month_year_label,
)


logger = logging.getLogger(__name__)


GEMINI_UNAVAILABLE_DETAIL = (
    "Could not generate an answer from the statement agent. "
    "Please try again."
)


router = APIRouter(
    prefix="/statement",
    tags=["Statement Q&A"],
)


class StatementQuestion(BaseModel):
    question: str
    statement_data: list[dict]


def _dump_transactions(
    transactions: list[dict],
) -> str:
    return json.dumps(
        transactions,
        ensure_ascii=False,
        default=str,
    )


def _call_gemini(prompt: str) -> str:
    try:
        answer = ask_gemini(prompt)

    except Exception as exc:
        status = (
            getattr(exc, "status_code", None)
            or getattr(exc, "code", None)
        )

        logger.error(
            "Gemini request failed: "
            "exception_type=%s status=%s",
            type(exc).__name__,
            status,
        )

        raise HTTPException(
            status_code=502,
            detail=GEMINI_UNAVAILABLE_DETAIL,
        )

    if answer is None or not str(answer).strip():
        logger.error(
            "Gemini returned an empty response."
        )

        raise HTTPException(
            status_code=502,
            detail=GEMINI_UNAVAILABLE_DETAIL,
        )

    return str(answer)


@router.post("/ask")
def ask_statement_question(
    request: StatementQuestion,
):

    parsed = extract_month_year(
        request.question
    )

    # ---------------------------------------------------------
    # MONTH / YEAR QUERY
    # ---------------------------------------------------------

    if parsed is not None:
        year, month = parsed

        label = month_year_label(
            year,
            month,
        )

        matching_rows = (
            filter_transactions_by_month_year(
                request.statement_data,
                year,
                month,
            )
        )

        # No transactions for requested month
        if not matching_rows:
            return {
                "question": request.question,
                "answer": (
                    f"No transactions found for {label}."
                ),
            }

        # First try deterministic calculation using ONLY
        # the requested month's transactions.
        deterministic_answer = (
            answer_deterministic_question(
                request.question,
                matching_rows,
            )
        )

        if deterministic_answer is not None:
            return {
                "question": request.question,
                "answer": deterministic_answer,
            }

        # Only open-ended month questions reach Gemini.
        prompt = f"""
You are analyzing a synthetic bank statement.

The user asked about {label}.

Use ONLY the {label} transactions provided below.

Do not invent transactions.
Do not invent dates.
Do not use transactions from another month or year.

{label} transactions:
{_dump_transactions(matching_rows)}

User question:
{request.question}

Answer only using the transactions shown above.
Keep the answer concise and clear.
"""

    # ---------------------------------------------------------
    # NON-MONTH QUERY
    # ---------------------------------------------------------

    else:
        # Try deterministic Q&A before Gemini.
        deterministic_answer = (
            answer_deterministic_question(
                request.question,
                request.statement_data,
            )
        )

        if deterministic_answer is not None:
            return {
                "question": request.question,
                "answer": deterministic_answer,
            }

        # Only open-ended questions reach Gemini.
        prompt = f"""
You are analyzing a synthetic bank statement.

Statement transactions:
{_dump_transactions(request.statement_data)}

User question:
{request.question}

Answer only using the statement data provided.
Do not invent transactions or dates.
Keep the answer concise and clear.
"""

    answer = _call_gemini(prompt)

    return {
        "question": request.question,
        "answer": answer,
    }
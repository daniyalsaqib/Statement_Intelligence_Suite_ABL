import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.db.policy_vector_store import (
    search_policy_documents,
)
from backend.app.services.llm_service import ask_llm


logger = logging.getLogger(__name__)


LLM_UNAVAILABLE_DETAIL = (
    "Could not generate an answer from the policy assistant. "
    "Please try again."
)


router = APIRouter(
    prefix="/policy",
    tags=["Policy Q&A"],
)


class PolicyQuestion(BaseModel):
    question: str


def _call_llm(prompt: str) -> str:
    try:
        answer = ask_llm(prompt)

    except Exception as exc:
        status = (
            getattr(exc, "status_code", None)
            or getattr(exc, "code", None)
        )

        logger.error(
            "LLM request failed: "
            "provider=groq exception_type=%s status=%s",
            type(exc).__name__,
            status,
        )

        raise HTTPException(
            status_code=502,
            detail=LLM_UNAVAILABLE_DETAIL,
        )

    if answer is None or not str(answer).strip():
        logger.error(
            "LLM provider returned an empty response."
        )

        raise HTTPException(
            status_code=502,
            detail=LLM_UNAVAILABLE_DETAIL,
        )

    return str(answer).strip()


@router.post("/ask")
def ask_policy_question(
    request: PolicyQuestion,
):

    # Retrieve relevant ABL public-policy chunks.
    results = search_policy_documents(
        request.question,
        limit=3,
    )

    # Smaller cosine distance means a better semantic match.
    relevant_results = [
        result
        for result in results
        if result["distance"] <= 0.75
    ]

    # Fail closed when the available policy corpus does not
    # contain sufficiently relevant information.
    if not relevant_results:
        return {
            "question": request.question,
            "answer": (
                "I could not find relevant information in the "
                "available Allied Bank public policy documents."
            ),
            "sources": [],
        }

    # Build context only from retrieved public ABL policy data.
    context = "\n\n".join(
        f"""
Title: {result["title"]}
Source: {result["source"]}
Content:
{result["content"]}
"""
        for result in relevant_results
    )

    prompt = f"""
You are an Allied Bank public-policy information assistant.

Answer the user's question ONLY using the retrieved policy context below.

Rules:
1. Do not use outside knowledge.
2. Do not invent Allied Bank policies.
3. If the context does not contain enough information, say that the available public policy documents do not provide enough information.
4. Keep the answer concise and clear.
5. Do not invent source URLs.

Retrieved policy context:
{context}

User question:
{request.question}
"""

    answer = _call_llm(prompt)

    # Return unique retrieval sources.
    sources = []

    for result in relevant_results:
        source = {
            "title": result["title"],
            "url": result["source"],
        }

        if source not in sources:
            sources.append(source)

    return {
        "question": request.question,
        "answer": answer,
        "sources": sources,
    }

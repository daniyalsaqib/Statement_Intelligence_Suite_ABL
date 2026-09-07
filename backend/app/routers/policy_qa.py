from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.db.policy_vector_store import search_policy_documents
from backend.app.services.gemini_service import ask_gemini


router = APIRouter(
    prefix="/policy",
    tags=["Policy Q&A"],
)


class PolicyQuestion(BaseModel):
    question: str


@router.post("/ask")
def ask_policy_question(request: PolicyQuestion):

    # Retrieve the most relevant ABL public-policy chunks
    results = search_policy_documents(
        request.question,
        limit=3,
    )

    # Keep only reasonably relevant results.
    # Smaller cosine distance means a better semantic match.
    relevant_results = [
        result
        for result in results
        if result["distance"] <= 0.75
    ]

    # Fail closed if the policy database has no relevant information
    if not relevant_results:
        return {
            "question": request.question,
            "answer": "I could not find relevant information in the available Allied Bank public policy documents.",
            "sources": [],
        }

    # Build context ONLY from retrieved ABL public-policy content
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

    answer = ask_gemini(prompt)

    # Return unique sources used by retrieval
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
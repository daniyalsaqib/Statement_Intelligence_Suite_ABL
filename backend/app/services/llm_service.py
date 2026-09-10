import os

from dotenv import load_dotenv
from groq import Groq


load_dotenv()


DEFAULT_GROQ_MODEL = "openai/gpt-oss-20b"


def ask_llm(prompt: str) -> str:
    """
    Generate a grounded banking-information response through Groq.

    GPT-OSS uses low reasoning effort because this application
    primarily needs fast, grounded summarization rather than
    extensive multi-step reasoning.
    """

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not configured."
        )

    model = (
        os.getenv(
            "GROQ_MODEL",
            DEFAULT_GROQ_MODEL,
        ).strip()
        or DEFAULT_GROQ_MODEL
    )

    client = Groq(
        api_key=api_key,
        timeout=15.0,
        max_retries=0,
    )

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a concise banking-information assistant. "
                    "Follow all grounding instructions supplied in the "
                    "user prompt exactly. "
                    "Treat verified backend facts as authoritative. "
                    "Do not invent financial information, currencies, "
                    "transactions, dates, totals, or policies. "
                    "Always return a clear final answer."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        reasoning_effort="low",
        temperature=0.0,
        max_completion_tokens=1600,
    )

    if not completion.choices:
        return ""

    content = (
        completion
        .choices[0]
        .message
        .content
    )

    if content is None:
        return ""

    return str(content).strip()
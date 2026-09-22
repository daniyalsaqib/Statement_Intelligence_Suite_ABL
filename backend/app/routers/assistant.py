from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator

from backend.app.models.statement import StatementLine
from backend.app.routers.policy_qa import (
    PolicyQuestion,
    ask_policy_question,
)
from backend.app.routers.statement_qa import (
    MAX_HISTORY_MESSAGES,
    MAX_QUESTION_CHARS,
    MAX_STATEMENT_ROWS,
    ConversationMessage,
    StatementQuestion,
    StatementTransactionInput,
    ask_statement_question,
)
from backend.app.services.subscription_analysis import (
    detect_recurring_payments,
)

router = APIRouter(
    prefix="/assistant",
    tags=["Assistant"],
)


# ---------------------------------------------------------
# UNIFIED ASSISTANT REQUEST
# ---------------------------------------------------------
#
# Is endpoint ka purpose existing statement, recurring,
# aur policy capabilities ko replace karna nahi hai.
#
# Ye unke upar aik thin orchestration layer hai.
#
# Existing endpoints backward-compatible rahenge:
#
# /statement/ask
# /statement/subscriptions
# /policy/ask
#
# Unified frontend eventually sirf /assistant/chat use kar sakta hai.


class AssistantQuestion(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )

    question: str = Field(
        min_length=1,
        max_length=MAX_QUESTION_CHARS,
    )

    # Policy questions statement ke baghair bhi chal sakte hain.
    # Statement / recurring capabilities ke liye ye data required
    # hoga, lekin request model mein optional-empty rakhna zaroori
    # hai taake unified endpoint policy-only requests bhi accept kare.
    statement_data: list[StatementTransactionInput] = Field(
        default_factory=list,
        max_length=MAX_STATEMENT_ROWS,
    )

    conversation_history: list[ConversationMessage] = Field(
        default_factory=list,
        max_length=MAX_HISTORY_MESSAGES,
    )

    @field_validator(
        "question",
        mode="before",
    )
    @classmethod
    def normalize_question(
        cls,
        value,
    ):
        if not isinstance(
            value,
            str,
        ):
            return value

        normalized = value.strip()

        if not normalized:
            raise ValueError("Question must not be blank.")

        return normalized


AssistantCapability = Literal[
    "statement",
    "recurring",
    "policy",
]


# ---------------------------------------------------------
# DETERMINISTIC CAPABILITY ROUTING
# ---------------------------------------------------------
#
# Hum LLM ko router nahi bana rahe.
#
# Reason:
# - routing predictable rehni chahiye
# - statement calculations ka trust boundary preserve rehna chahiye
# - recurring rules deterministic hi rehne chahiye
# - policy RAG sirf policy capability ke andar chale
#
# Strong policy phrases ko pehle check karte hain.
# Agar statement loaded hai aur koi strong policy / recurring
# signal nahi hai, default statement intelligence hai.


POLICY_PHRASES = (
    "policy",
    "policies",
    "public policy",
    "abl policy",
    "allied bank policy",
    "unclaimed deposit",
    "unclaimed deposits",
    "required documents",
    "documents are required",
    "documents required",
    "eligibility",
    "eligible for",
    "terms and conditions",
    "complaint procedure",
    "complaint process",
    "grievance",
    "claim procedure",
    "claim process",
)


RECURRING_PHRASES = (
    "recurring",
    "subscription",
    "subscriptions",
    "repeated payment",
    "repeated payments",
    "repeat payment",
    "repeat payments",
    "repeated debit",
    "repeated debits",
    "same merchant",
    "same merchants",
    "monthly payment",
    "monthly payments",
)


def _normalize_question(
    question: str,
) -> str:
    return " ".join(question.lower().split())


def _contains_any_phrase(
    question: str,
    phrases: tuple[str, ...],
) -> bool:
    normalized = _normalize_question(question)

    return any(phrase in normalized for phrase in phrases)


def resolve_assistant_capability(
    question: str,
    has_statement_data: bool,
) -> AssistantCapability:
    """
    Pick one internal capability without asking the LLM
    to make a financial-routing decision.

    Strong policy wording wins first.

    Recurring wording wins second.

    Otherwise, when a statement is loaded, the assistant
    treats the question as statement intelligence.

    If no statement is loaded and no policy signal exists,
    we still resolve to statement so the user receives the
    correct "analyze a statement first" error instead of
    silently sending a personal-finance question to policy RAG.
    """

    if _contains_any_phrase(
        question,
        POLICY_PHRASES,
    ):
        return "policy"

    if _contains_any_phrase(
        question,
        RECURRING_PHRASES,
    ):
        return "recurring"

    if has_statement_data:
        return "statement"

    return "statement"


# ---------------------------------------------------------
# RESPONSE HELPERS
# ---------------------------------------------------------


def _format_recurring_answer(
    recurring_payments: list[dict],
) -> str:
    if not recurring_payments:
        return (
            "No recurring payment candidates were detected "
            "in the uploaded statement."
        )

    candidate_summaries = []

    for payment in recurring_payments:
        candidate_summaries.append(
            (f'{payment["description"]} ' f'({payment["occurrences"]} occurrences)')
        )

    joined = ", ".join(candidate_summaries)

    return (
        f"Detected {len(recurring_payments)} "
        f"recurring-payment candidate"
        f'{"s" if len(recurring_payments) != 1 else ""}: '
        f"{joined}."
    )


# ---------------------------------------------------------
# UNIFIED CHAT ENDPOINT
# ---------------------------------------------------------


@router.post("/chat")
def assistant_chat(
    request: AssistantQuestion,
):
    capability = resolve_assistant_capability(
        request.question,
        bool(request.statement_data),
    )

    # -----------------------------------------------------
    # POLICY RAG
    # -----------------------------------------------------

    if capability == "policy":
        policy_result = ask_policy_question(
            PolicyQuestion(
                question=request.question,
            )
        )

        return {
            "question": request.question,
            "capability": "policy",
            "method": "policy_rag",
            "answer": policy_result["answer"],
            "sources": policy_result.get(
                "sources",
                [],
            ),
            "structured_data": None,
        }

    # Statement-backed capabilities require an analyzed
    # statement from the current workspace.
    if not request.statement_data:
        raise HTTPException(
            status_code=400,
            detail=(
                "Analyze a synthetic statement before asking "
                "statement or recurring-payment questions."
            ),
        )

    # -----------------------------------------------------
    # RECURRING PAYMENTS
    # -----------------------------------------------------

    if capability == "recurring":
        transactions = [
            StatementLine(**row.model_dump()) for row in request.statement_data
        ]

        recurring_payments = detect_recurring_payments(transactions)

        return {
            "question": request.question,
            "capability": "recurring",
            "method": "deterministic_recurring_rules",
            "answer": _format_recurring_answer(recurring_payments),
            "sources": [],
            "structured_data": {
                "recurring_payment_count": len(recurring_payments),
                "recurring_payments": (recurring_payments),
            },
        }

    # -----------------------------------------------------
    # STATEMENT INTELLIGENCE
    # -----------------------------------------------------
    #
    # Existing statement QA remains the source of truth.
    # Unified routing does NOT duplicate financial arithmetic.

    statement_result = ask_statement_question(
        StatementQuestion(
            question=request.question,
            statement_data=[row.model_dump() for row in request.statement_data],
            conversation_history=(request.conversation_history),
        )
    )

    return {
        "question": request.question,
        "capability": "statement",
        "method": "verified_statement_intelligence",
        "answer": statement_result["answer"],
        "sources": [],
        "structured_data": None,
    }

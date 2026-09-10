import json
import logging
import re
from calendar import month_name

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.services.llm_service import ask_llm
from backend.app.services.statement_facts import (
    build_verified_statement_facts,
)
from backend.app.services.statement_qa_deterministic import (
    answer_deterministic_question,
)
from backend.app.services.statement_qa_filter import (
    extract_month_year,
    filter_transactions_by_month_year,
    month_year_label,
)


logger = logging.getLogger(__name__)


LLM_UNAVAILABLE_DETAIL = (
    "Could not generate an answer from the statement agent. "
    "Please try again."
)


router = APIRouter(
    prefix="/statement",
    tags=["Statement Q&A"],
)


MONTH_ALIASES = {
    1: ("january", "jan"),
    2: ("february", "feb"),
    3: ("march", "mar"),
    4: ("april", "apr"),
    5: ("may",),
    6: ("june", "jun"),
    7: ("july", "jul"),
    8: ("august", "aug"),
    9: ("september", "sep", "sept"),
    10: ("october", "oct"),
    11: ("november", "nov"),
    12: ("december", "dec"),
}


OPEN_ENDED_TERMS = (
    "summarize",
    "summary",
    "compare",
    "comparison",
    "pattern",
    "patterns",
    "trend",
    "trends",
    "stand out",
    "stands out",
    "standing out",
    "analyze",
    "analysis",
    "explain",
    "overview",
    "insight",
    "insights",
    "what do you notice",
    "what can you tell",
    "tell me about",
)


class StatementQuestion(BaseModel):
    question: str
    statement_data: list[dict]


def _dump_json(
    value: object,
) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        default=str,
        indent=2,
    )


def _format_amount(
    value,
) -> str:
    return f"{float(value):,.2f}"


def _requires_open_ended_analysis(
    question: str,
) -> bool:
    """
    Determine whether the question asks for interpretation,
    summarization, comparison, or multiple pieces of information.

    Such questions must not be short-circuited by the deterministic
    helper merely because they also contain phrases such as
    "total spending".
    """

    question_lower = question.lower()

    if any(
        term in question_lower
        for term in OPEN_ENDED_TERMS
    ):
        return True

    # Compound questions commonly request more than one result.
    # Examples:
    # "How much did I spend and what was my closing balance?"
    # "Give me the total and tell me what stands out."
    if " and " in question_lower:
        return True

    return False


def _mentioned_month_numbers(
    question: str,
) -> list[int]:
    question_lower = question.lower()

    found_months = []

    for month_number, aliases in MONTH_ALIASES.items():
        for alias in aliases:
            pattern = rf"\b{re.escape(alias)}\b"

            if re.search(
                pattern,
                question_lower,
            ):
                found_months.append(
                    month_number
                )
                break

    return found_months


def _wants_total_spending(
    question: str,
) -> bool:
    question_lower = question.lower()

    phrases = (
        "total spending",
        "total spend",
        "overall spending",
        "overall spend",
        "spent in total",
        "include the total",
        "mention the total",
        "mention my total",
    )

    return any(
        phrase in question_lower
        for phrase in phrases
    )


def _wants_comparison(
    question: str,
) -> bool:
    question_lower = question.lower()

    comparison_terms = (
        "compare",
        "comparison",
        "versus",
        " vs ",
        "between",
        "higher",
        "lower",
        "more than",
        "less than",
    )

    return any(
        term in question_lower
        for term in comparison_terms
    )


def _month_spending_entries(
    verified_facts: dict,
    requested_months: list[int],
) -> list[dict]:

    spending_by_month = verified_facts.get(
        "spending_by_month",
        {},
    )

    entries = []

    for requested_month in requested_months:

        for key, amount in spending_by_month.items():

            try:
                year_text, month_text = key.split(
                    "-",
                    maxsplit=1,
                )

                year = int(year_text)
                month_number = int(month_text)

            except (
                ValueError,
                AttributeError,
            ):
                continue

            if month_number != requested_month:
                continue

            entries.append(
                {
                    "year": year,
                    "month": month_number,
                    "label": (
                        f"{month_name[month_number]} "
                        f"{year}"
                    ),
                    "amount": float(amount),
                }
            )

    return entries


def _build_verified_figure_block(
    question: str,
    verified_facts: dict,
    scope_label: str | None = None,
) -> str:

    lines = []

    if _wants_total_spending(
        question
    ):
        total_debit = verified_facts.get(
            "total_debit"
        )

        if total_debit is not None:

            if scope_label:
                lines.append(
                    f"Total spending for "
                    f"{scope_label}: "
                    f"{_format_amount(total_debit)}."
                )

            else:
                lines.append(
                    f"Total spending: "
                    f"{_format_amount(total_debit)}."
                )

    requested_months = (
        _mentioned_month_numbers(
            question
        )
    )

    month_entries = (
        _month_spending_entries(
            verified_facts,
            requested_months,
        )
    )

    if (
        _wants_comparison(question)
        and month_entries
    ):
        for entry in month_entries:
            lines.append(
                f"{entry['label']} spending: "
                f"{_format_amount(entry['amount'])}."
            )

        if len(month_entries) == 2:
            first = month_entries[0]
            second = month_entries[1]

            if first["amount"] > second["amount"]:
                lines.append(
                    f"{first['label']} spending was "
                    f"higher than "
                    f"{second['label']} spending."
                )

            elif first["amount"] < second["amount"]:
                lines.append(
                    f"{second['label']} spending was "
                    f"higher than "
                    f"{first['label']} spending."
                )

            else:
                lines.append(
                    f"{first['label']} and "
                    f"{second['label']} had equal spending."
                )

    if not lines:
        return ""

    return (
        "Verified figures:\n"
        + "\n".join(
            f"- {line}"
            for line in lines
        )
    )


def _numeric_guard_instruction(
    verified_figure_block: str,
) -> str:

    if not verified_figure_block:
        return ""

    return """
The backend will attach the requested verified numeric figures
to your response separately.

Do NOT state numeric amounts, percentages, currency symbols,
currency names, or numeric dates in your response.

Do NOT repeat or recalculate the verified figures.

Focus only on qualitative interpretation that is supported
by the verified facts and transactions.
"""


def _contains_numeric_or_currency(
    text: str,
) -> bool:

    if re.search(
        r"\d",
        text,
    ):
        return True

    currency_pattern = (
        r"(?i)"
        r"(\$|€|£|¥|"
        r"\bUSD\b|"
        r"\bPKR\b|"
        r"\bEUR\b|"
        r"\bGBP\b|"
        r"\brupees?\b)"
    )

    return bool(
        re.search(
            currency_pattern,
            text,
        )
    )


def _combine_verified_and_llm_answer(
    verified_figure_block: str,
    llm_answer: str,
) -> str:

    if not verified_figure_block:
        return llm_answer

    # If verified numeric information is being supplied by Python,
    # the LLM may contribute only qualitative commentary.
    #
    # If the provider produces any numeric/currency information,
    # discard that commentary rather than risk presenting an
    # incorrect financial value.
    if _contains_numeric_or_currency(
        llm_answer
    ):
        logger.warning(
            "Discarding numeric LLM commentary because "
            "verified backend figures are authoritative."
        )

        return verified_figure_block

    if not llm_answer.strip():
        return verified_figure_block

    return (
        f"{verified_figure_block}\n\n"
        f"{llm_answer.strip()}"
    )


def _call_llm(
    prompt: str,
) -> str:
    try:
        answer = ask_llm(
            prompt
        )

    except Exception as exc:
        status = (
            getattr(
                exc,
                "status_code",
                None,
            )
            or getattr(
                exc,
                "code",
                None,
            )
        )

        logger.error(
            "LLM request failed: "
            "provider=groq "
            "exception_type=%s "
            "status=%s",
            type(exc).__name__,
            status,
        )

        raise HTTPException(
            status_code=502,
            detail=LLM_UNAVAILABLE_DETAIL,
        )

    if (
        answer is None
        or not str(answer).strip()
    ):
        logger.error(
            "LLM provider returned an empty response."
        )

        raise HTTPException(
            status_code=502,
            detail=LLM_UNAVAILABLE_DETAIL,
        )

    return str(
        answer
    ).strip()


@router.post("/ask")
def ask_statement_question(
    request: StatementQuestion,
):

    parsed = extract_month_year(
        request.question
    )

    requires_open_ended = (
        _requires_open_ended_analysis(
            request.question
        )
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

        if not matching_rows:
            return {
                "question": request.question,
                "answer": (
                    f"No transactions found for "
                    f"{label}."
                ),
            }

        # Only simple exact questions are allowed to exit through
        # the deterministic helper.
        #
        # Open-ended or compound questions continue into the
        # verified-facts + LLM pipeline.
        if not requires_open_ended:
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

        verified_facts = (
            build_verified_statement_facts(
                matching_rows
            )
        )

        verified_figure_block = (
            _build_verified_figure_block(
                request.question,
                verified_facts,
                scope_label=label,
            )
        )

        numeric_guard = (
            _numeric_guard_instruction(
                verified_figure_block
            )
        )

        prompt = f"""
You are analyzing a synthetic bank statement.

The user asked specifically about {label}.

Use ONLY the verified backend facts and the {label}
transactions supplied below.

VERIFIED BACKEND FACTS:
{_dump_json(verified_facts)}

{label} TRANSACTIONS:
{_dump_json(matching_rows)}

IMPORTANT RULES:

1. The VERIFIED BACKEND FACTS were calculated deterministically
   by the backend and are authoritative.

2. Never contradict the verified backend facts.

3. Do not independently recalculate totals, balances, counts,
   monthly totals, merchant totals, largest debits, or largest
   credits.

4. Do not invent a currency symbol or currency name.

5. Do not invent transactions, dates, merchants, balances,
   debits, credits, categories, subscriptions, or financial facts.

6. Do not use transactions from another month or year.

7. Claims such as largest, highest, lowest, majority, most,
   main, or similar comparative claims must be supported by
   the verified facts or supplied transactions.

8. Answer every part of the user's question that can be
   supported by the supplied information.

9. If information is insufficient, state that instead of guessing.

10. Keep the answer concise and suitable for a banking
    statement analysis interface.

{numeric_guard}

User question:
{request.question}

Answer only from the information supplied above.
"""

    # ---------------------------------------------------------
    # NON-MONTH QUERY
    # ---------------------------------------------------------

    else:

        # Only simple exact questions should short-circuit through
        # the deterministic helper.
        if not requires_open_ended:
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

        verified_facts = (
            build_verified_statement_facts(
                request.statement_data
            )
        )

        verified_figure_block = (
            _build_verified_figure_block(
                request.question,
                verified_facts,
            )
        )

        numeric_guard = (
            _numeric_guard_instruction(
                verified_figure_block
            )
        )

        prompt = f"""
You are analyzing a synthetic bank statement.

Use ONLY the verified backend facts and statement transactions
supplied below.

VERIFIED BACKEND FACTS:
{_dump_json(verified_facts)}

STATEMENT TRANSACTIONS:
{_dump_json(request.statement_data)}

IMPORTANT RULES:

1. The VERIFIED BACKEND FACTS were calculated deterministically
   by the backend and are authoritative.

2. Never contradict the verified backend facts.

3. Do not independently recalculate totals, balances, counts,
   monthly totals, merchant totals, largest debits, or largest
   credits.

4. Do not invent a currency symbol or currency name.

5. Do not invent transactions, dates, merchants, balances,
   debits, credits, categories, subscriptions, or financial facts.

6. Claims such as largest, highest, lowest, majority, most,
   main, or similar comparative claims must be supported by
   the verified facts or supplied transactions.

7. Answer every part of the user's question that can be
   supported by the supplied information.

8. If information is insufficient, state that instead of guessing.

9. Keep the answer concise and suitable for a banking
   statement analysis interface.

{numeric_guard}

User question:
{request.question}

Answer only from the information supplied above.
"""

    llm_answer = _call_llm(
        prompt
    )

    final_answer = (
        _combine_verified_and_llm_answer(
            verified_figure_block,
            llm_answer,
        )
    )

    return {
        "question": request.question,
        "answer": final_answer,
    }
from backend.app.models.statement import StatementLine
from backend.app.services.statement_analysis import analyze_statement

TOTAL_SPENDING_PHRASES = (
    "total spending",
    "total spend",
    "overall spending",
    "overall spend",
    "spent in total",
    "total amount spent",
    "how much did i spend",
    "how much have i spent",
    "total debit",
    "total debits",
    # Natural financial-language alternatives.
    "total expenditure",
    "overall expenditure",
    "what was my expenditure",
    "how much was my expenditure",
    "total outflow",
    "total outflows",
    "how much money went out",
    "how much went out",
    "how much did i pay out",
    "how much have i paid out",
    "what were my outflows",
)


TOTAL_CREDIT_PHRASES = (
    "how much money did i receive",
    "how much did i receive",
    "how much have i received",
    "total received",
    "total credit",
    "total credits",
    "total income",
    # Natural inflow alternatives.
    "total inflow",
    "total inflows",
    "how much money came in",
    "how much came in",
    "what were my inflows",
)


def _to_statement_lines(
    statement_data: list[dict],
) -> list[StatementLine]:
    return [StatementLine(**row) for row in statement_data]


def is_specific_spending_question(
    question: str,
) -> bool:
    """
    Detect spending questions that target a specific merchant
    or description instead of the whole statement.

    Examples:
    - How much did I spend on Netflix?
    - How much did I spend at Grocery Store?

    IMPORTANT:
    A targeted spending question must never be interpreted as
    "total statement spending" only because it contains the
    phrase "how much did I spend".
    """

    normalized = f" {' '.join(question.lower().strip().split())} "

    has_spending_intent = any(phrase in normalized for phrase in TOTAL_SPENDING_PHRASES)

    if not has_spending_intent:
        return False

    return any(
        marker in normalized
        for marker in (
            " on ",
            " at ",
            " to ",
        )
    )


def _answer_specific_spending_question(
    question: str,
    transactions: list[StatementLine],
) -> str | None:
    """
    Deterministically answer merchant-specific spending when
    exactly one transaction description from the current
    statement scope is explicitly mentioned in the question.

    If no safe unique description match exists, return None
    instead of incorrectly returning total statement spending.
    """

    if not is_specific_spending_question(question):
        return None

    normalized_question = " ".join(question.lower().strip().split())

    matched_descriptions: dict[str, str] = {}

    for transaction in transactions:
        normalized_description = " ".join(
            transaction.description.lower().strip().split()
        )

        if not normalized_description:
            continue

        if normalized_description not in normalized_question:
            continue

        matched_descriptions.setdefault(
            normalized_description,
            transaction.description,
        )

    # Safe deterministic answer sirf tab dena hai jab exactly
    # one statement description question mein clearly match ho.
    if len(matched_descriptions) != 1:
        return None

    normalized_description, display_description = next(
        iter(matched_descriptions.items())
    )

    total = sum(
        transaction.debit or 0
        for transaction in transactions
        if " ".join(transaction.description.lower().strip().split())
        == normalized_description
    )

    return f"Your spending on {display_description} is " f"{total:,.2f}."


def answer_deterministic_question(
    question: str,
    statement_data: list[dict],
) -> str | None:

    normalized = " ".join(question.lower().strip().split())

    transactions = _to_statement_lines(statement_data)

    if not transactions:
        return "No transactions are available in the uploaded statement."

    analysis = analyze_statement(transactions)

    # ---------------------------------------------------------
    # TRANSACTION COUNTS
    # ---------------------------------------------------------

    if (
        "how many debit transactions" in normalized
        or "number of debit transactions" in normalized
        or "debit transaction count" in normalized
    ):
        count = sum(
            1
            for transaction in transactions
            if transaction.debit is not None and transaction.debit != 0
        )

        return f"There are {count} debit transactions."

    if (
        "how many credit transactions" in normalized
        or "number of credit transactions" in normalized
        or "credit transaction count" in normalized
    ):
        count = sum(
            1
            for transaction in transactions
            if transaction.credit is not None and transaction.credit != 0
        )

        return f"There are {count} credit transactions."

    if (
        "how many transactions" in normalized
        or "number of transactions" in normalized
        or "transaction count" in normalized
    ):
        return (
            f"This statement contains " f"{analysis['transaction_count']} transactions."
        )

        # ---------------------------------------------------------
    # TOTAL SPENDING / DEBITS
    # ---------------------------------------------------------
    #
    # IMPORTANT:
    # Spending intent ki saari natural-language phrases
    # upar TOTAL_SPENDING_PHRASES mein centralized hain.
    #
    # Isse deterministic calculation aur verified-figure
    # guard future mein same vocabulary use kar sakte hain.
    #
    # Financial amount hamesha Python analysis se aata hai,
    # LLM se calculate nahi hota.

    # Merchant-specific spending must be resolved before the
    # generic total-spending rule.
    #
    # Example:
    # "How much did I spend on Netflix?"
    #
    # must not return the total debit for the whole statement.
    specific_spending_answer = _answer_specific_spending_question(
        question,
        transactions,
    )

    if specific_spending_answer is not None:
        return specific_spending_answer

    # If the question targets a merchant but we could not
    # safely identify exactly one description, do NOT fall
    # through to the whole-statement spending total.
    if is_specific_spending_question(question):
        return None

    if any(phrase in normalized for phrase in TOTAL_SPENDING_PHRASES):
        return f"Your total spending is " f"{analysis['total_debit']:,.2f}."

    # ---------------------------------------------------------
    # TOTAL RECEIVED / CREDITS
    # ---------------------------------------------------------
    #
    # Incoming-money intent ki natural-language phrases
    # TOTAL_CREDIT_PHRASES mein centralized hain.
    #
    # Same rule:
    # verified credit total Python se calculate hota hai.

    if any(phrase in normalized for phrase in TOTAL_CREDIT_PHRASES):
        return f"Your total credits are " f"{analysis['total_credit']:,.2f}."

    # ---------------------------------------------------------
    # BALANCES
    # ---------------------------------------------------------

    if "opening balance" in normalized:
        value = analysis["opening_balance"]

        if value is None:
            return "The opening balance is not available."

        return f"Your opening balance is " f"{value:,.2f}."

    if "closing balance" in normalized:
        value = analysis["closing_balance"]

        if value is None:
            return "The closing balance is not available."

        return f"Your closing balance is " f"{value:,.2f}."

    # ---------------------------------------------------------
    # LARGEST DEBIT
    # ---------------------------------------------------------

    if (
        "largest debit" in normalized
        or "biggest debit" in normalized
        or "highest debit" in normalized
    ):
        debit_rows = [
            transaction
            for transaction in transactions
            if transaction.debit is not None and transaction.debit != 0
        ]

        if not debit_rows:
            return "No debit transactions were found."

        largest = max(
            debit_rows,
            key=lambda transaction: transaction.debit or 0,
        )

        return (
            f"Your largest debit transaction was "
            f"{largest.debit:,.2f} "
            f"on {largest.date.isoformat()} "
            f"for {largest.description}."
        )

    # ---------------------------------------------------------
    # LARGEST CREDIT
    # ---------------------------------------------------------

    if (
        "largest credit" in normalized
        or "biggest credit" in normalized
        or "highest credit" in normalized
    ):
        credit_rows = [
            transaction
            for transaction in transactions
            if transaction.credit is not None and transaction.credit != 0
        ]

        if not credit_rows:
            return "No credit transactions were found."

        largest = max(
            credit_rows,
            key=lambda transaction: transaction.credit or 0,
        )

        return (
            f"Your largest credit transaction was "
            f"{largest.credit:,.2f} "
            f"on {largest.date.isoformat()} "
            f"for {largest.description}."
        )

    return None

from backend.app.models.statement import StatementLine
from backend.app.services.statement_analysis import analyze_statement


def _to_statement_lines(
    statement_data: list[dict],
) -> list[StatementLine]:
    return [
        StatementLine(**row)
        for row in statement_data
    ]


def answer_deterministic_question(
    question: str,
    statement_data: list[dict],
) -> str | None:

    normalized = " ".join(
        question.lower().strip().split()
    )

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
            if transaction.debit is not None
            and transaction.debit != 0
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
            if transaction.credit is not None
            and transaction.credit != 0
        )

        return f"There are {count} credit transactions."

    if (
        "how many transactions" in normalized
        or "number of transactions" in normalized
        or "transaction count" in normalized
    ):
        return (
            f"This statement contains "
            f"{analysis['transaction_count']} transactions."
        )

    # ---------------------------------------------------------
    # TOTAL SPENDING / DEBITS
    # ---------------------------------------------------------

    if (
        "total spending" in normalized
        or "total spend" in normalized
        or "how much did i spend" in normalized
        or "how much have i spent" in normalized
        or "total debit" in normalized
        or "total debits" in normalized
    ):
        return (
            f"Your total spending is "
            f"{analysis['total_debit']:,.2f}."
        )

    # ---------------------------------------------------------
    # TOTAL RECEIVED / CREDITS
    # ---------------------------------------------------------

    if (
        "how much money did i receive" in normalized
        or "how much did i receive" in normalized
        or "how much have i received" in normalized
        or "total received" in normalized
        or "total credit" in normalized
        or "total credits" in normalized
        or "total income" in normalized
    ):
        return (
            f"Your total credits are "
            f"{analysis['total_credit']:,.2f}."
        )

    # ---------------------------------------------------------
    # BALANCES
    # ---------------------------------------------------------

    if "opening balance" in normalized:
        value = analysis["opening_balance"]

        if value is None:
            return "The opening balance is not available."

        return (
            f"Your opening balance is "
            f"{value:,.2f}."
        )

    if "closing balance" in normalized:
        value = analysis["closing_balance"]

        if value is None:
            return "The closing balance is not available."

        return (
            f"Your closing balance is "
            f"{value:,.2f}."
        )

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
            if transaction.debit is not None
            and transaction.debit != 0
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
            if transaction.credit is not None
            and transaction.credit != 0
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
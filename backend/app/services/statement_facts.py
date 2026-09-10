from collections import defaultdict

from backend.app.models.statement import (
    StatementLine,
)
from backend.app.services.statement_analysis import (
    analyze_statement,
)


def _money(
    value,
):
    if value is None:
        return None

    return round(
        float(value),
        2,
    )


def build_verified_statement_facts(
    statement_data: list[dict],
) -> dict:

    transactions = [
        StatementLine(**row)
        for row in statement_data
    ]

    analysis = analyze_statement(
        transactions
    )

    debit_rows = [
        transaction
        for transaction in transactions
        if (
            transaction.debit is not None
            and transaction.debit != 0
        )
    ]

    credit_rows = [
        transaction
        for transaction in transactions
        if (
            transaction.credit is not None
            and transaction.credit != 0
        )
    ]

    spending_by_month = defaultdict(float)
    credits_by_month = defaultdict(float)
    spending_by_description = defaultdict(float)

    for transaction in transactions:
        month = transaction.date.strftime(
            "%Y-%m"
        )

        if (
            transaction.debit is not None
            and transaction.debit != 0
        ):
            spending_by_month[month] += (
                transaction.debit
            )

            spending_by_description[
                transaction.description
            ] += transaction.debit

        if (
            transaction.credit is not None
            and transaction.credit != 0
        ):
            credits_by_month[month] += (
                transaction.credit
            )

    largest_debit = None

    if debit_rows:
        row = max(
            debit_rows,
            key=lambda transaction:
                transaction.debit or 0,
        )

        largest_debit = {
            "date": row.date.isoformat(),
            "description": row.description,
            "amount": _money(row.debit),
        }

    largest_credit = None

    if credit_rows:
        row = max(
            credit_rows,
            key=lambda transaction:
                transaction.credit or 0,
        )

        largest_credit = {
            "date": row.date.isoformat(),
            "description": row.description,
            "amount": _money(row.credit),
        }

    return {
        "transaction_count":
            analysis["transaction_count"],

        "debit_transaction_count":
            len(debit_rows),

        "credit_transaction_count":
            len(credit_rows),

        "total_debit":
            _money(
                analysis["total_debit"]
            ),

        "total_credit":
            _money(
                analysis["total_credit"]
            ),

        "opening_balance":
            _money(
                analysis["opening_balance"]
            ),

        "closing_balance":
            _money(
                analysis["closing_balance"]
            ),

        "spending_by_month": {
            month: _money(amount)
            for month, amount
            in sorted(
                spending_by_month.items()
            )
        },

        "credits_by_month": {
            month: _money(amount)
            for month, amount
            in sorted(
                credits_by_month.items()
            )
        },

        "spending_by_description": {
            description: _money(amount)
            for description, amount
            in sorted(
                spending_by_description.items()
            )
        },

        "largest_debit":
            largest_debit,

        "largest_credit":
            largest_credit,
    }

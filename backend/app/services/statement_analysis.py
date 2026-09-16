from backend.app.models.statement import StatementLine


def analyze_statement(
    transactions: list[StatementLine],
) -> dict:
    if not transactions:
        return {
            "transaction_count": 0,
            "total_debit": 0,
            "total_credit": 0,
            "opening_balance": None,
            "closing_balance": None,
        }

    total_debit = sum(
        transaction.debit or 0
        for transaction in transactions
    )

    total_credit = sum(
        transaction.credit or 0
        for transaction in transactions
    )

    return {
        "transaction_count": len(transactions),
        "total_debit": total_debit,
        "total_credit": total_credit,
        "opening_balance": transactions[0].balance,
        "closing_balance": transactions[-1].balance,
    }
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

    total_debit = sum(transaction.debit or 0 for transaction in transactions)

    total_credit = sum(transaction.credit or 0 for transaction in transactions)

    # ---------------------------------------------------------
    # CHRONOLOGICAL BALANCE BOUNDARY
    # ---------------------------------------------------------
    #
    # Uploaded CSV files may be ordered oldest-first or
    # newest-first.
    #
    # Opening / closing balances must therefore depend on
    # transaction dates, not raw CSV row position.
    #
    # Python's sort is stable, so transactions that share the
    # same date retain their original relative order.
    chronological_transactions = sorted(
        transactions,
        key=lambda transaction: transaction.date,
    )

    return {
        "transaction_count": len(transactions),
        "total_debit": total_debit,
        "total_credit": total_credit,
        "opening_balance": chronological_transactions[0].balance,
        "closing_balance": chronological_transactions[-1].balance,
    }

from collections import defaultdict

from backend.app.models.statement import StatementLine


def detect_recurring_payments(transactions: list[StatementLine]) -> list[dict]:

    # Group debit transactions by description/merchant
    grouped_transactions = defaultdict(list)

    for transaction in transactions:

        # Recurring payments should normally be outgoing payments
        if transaction.debit is not None:
            grouped_transactions[transaction.description.lower()].append(transaction)

    recurring_payments = []

    # If the same merchant appears more than once,
    # treat it as a recurring-payment candidate
    for description, items in grouped_transactions.items():

        if len(items) > 1:

            recurring_payments.append({
                "description": items[0].description,
                "occurrences": len(items),
                "amounts": [item.debit for item in items],
                "dates": [item.date for item in items],
            })

    return recurring_payments
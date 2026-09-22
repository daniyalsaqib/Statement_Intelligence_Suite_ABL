from collections import defaultdict

from backend.app.models.statement import StatementLine


def _normalize_description(
    description: str,
) -> str:
    """
    Normalize merchant descriptions for recurring-payment
    candidate grouping.

    Case differences and insignificant whitespace should not
    create separate merchant groups.
    """
    return " ".join(description.split()).casefold()


def _display_description(
    description: str,
) -> str:
    return " ".join(description.split())


def detect_recurring_payments(
    transactions: list[StatementLine],
) -> list[dict]:

    grouped_transactions = defaultdict(list)

    for transaction in transactions:

        # A recurring payment candidate must represent an
        # actual outgoing payment. Zero-value and negative
        # debit entries are not treated as recurring charges.
        if transaction.debit is None or transaction.debit <= 0:
            continue

        normalized_description = _normalize_description(transaction.description)

        # Blank descriptions cannot identify a merchant.
        if not normalized_description:
            continue

        grouped_transactions[normalized_description].append(transaction)

    recurring_payments = []

    for items in grouped_transactions.values():

        if len(items) <= 1:
            continue

        recurring_payments.append(
            {
                "description": (_display_description(items[0].description)),
                "occurrences": len(items),
                "amounts": [item.debit for item in items],
                "dates": [item.date for item in items],
            }
        )

    return recurring_payments

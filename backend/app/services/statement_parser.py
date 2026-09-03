import csv
import io

from backend.app.models.statement import StatementLine


def parse_statement_csv(file_content: bytes) -> list[StatementLine]:
    text = file_content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))

    transactions = []

    for row in reader:
        transaction = StatementLine(
            date=row["date"],
            description=row["description"],
            debit=float(row["debit"]) if row["debit"] else None,
            credit=float(row["credit"]) if row["credit"] else None,
            balance=float(row["balance"]),
        )

        transactions.append(transaction)

    return transactions
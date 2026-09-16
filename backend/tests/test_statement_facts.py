import unittest

from backend.app.services.statement_facts import (
    build_verified_statement_facts,
)


def row(
    date_value,
    description,
    debit=None,
    credit=None,
    balance=0.0,
):
    return {
        "date": date_value,
        "description": description,
        "debit": debit,
        "credit": credit,
        "balance": balance,
    }


class TestVerifiedStatementFactsRegressions(
    unittest.TestCase
):

    def test_empty_statement_facts(self):
        facts = build_verified_statement_facts(
            []
        )

        self.assertEqual(
            facts["transaction_count"],
            0,
        )

        self.assertEqual(
            facts["total_debit"],
            0.0,
        )

        self.assertEqual(
            facts["total_credit"],
            0.0,
        )

        self.assertIsNone(
            facts["opening_balance"]
        )

        self.assertIsNone(
            facts["closing_balance"]
        )

    def test_direction_counts(self):
        facts = build_verified_statement_facts(
            [
                row(
                    "2026-08-01",
                    "Debit A",
                    debit=100.0,
                    balance=900.0,
                ),
                row(
                    "2026-08-02",
                    "Credit",
                    credit=200.0,
                    balance=1100.0,
                ),
                row(
                    "2026-08-03",
                    "Debit B",
                    debit=50.0,
                    balance=1050.0,
                ),
            ]
        )

        self.assertEqual(
            facts[
                "debit_transaction_count"
            ],
            2,
        )

        self.assertEqual(
            facts[
                "credit_transaction_count"
            ],
            1,
        )

    def test_monthly_spending(self):
        facts = build_verified_statement_facts(
            [
                row(
                    "2026-07-01",
                    "A",
                    debit=100.0,
                    balance=900.0,
                ),
                row(
                    "2026-07-02",
                    "B",
                    debit=50.0,
                    balance=850.0,
                ),
                row(
                    "2026-08-01",
                    "C",
                    debit=200.0,
                    balance=650.0,
                ),
            ]
        )

        self.assertEqual(
            facts[
                "spending_by_month"
            ],
            {
                "2026-07": 150.0,
                "2026-08": 200.0,
            },
        )

    def test_monthly_credits(self):
        facts = build_verified_statement_facts(
            [
                row(
                    "2026-07-01",
                    "Salary",
                    credit=1000.0,
                    balance=1000.0,
                ),
                row(
                    "2026-08-01",
                    "Transfer",
                    credit=200.0,
                    balance=1200.0,
                ),
            ]
        )

        self.assertEqual(
            facts[
                "credits_by_month"
            ],
            {
                "2026-07": 1000.0,
                "2026-08": 200.0,
            },
        )

    def test_largest_debit(self):
        facts = build_verified_statement_facts(
            [
                row(
                    "2026-08-01",
                    "Small",
                    debit=100.0,
                    balance=900.0,
                ),
                row(
                    "2026-08-02",
                    "Large",
                    debit=500.0,
                    balance=400.0,
                ),
            ]
        )

        self.assertEqual(
            facts["largest_debit"],
            {
                "date": "2026-08-02",
                "description": "Large",
                "amount": 500.0,
            },
        )

    def test_largest_credit(self):
        facts = build_verified_statement_facts(
            [
                row(
                    "2026-08-01",
                    "Small",
                    credit=100.0,
                    balance=100.0,
                ),
                row(
                    "2026-08-02",
                    "Salary",
                    credit=500.0,
                    balance=600.0,
                ),
            ]
        )

        self.assertEqual(
            facts["largest_credit"],
            {
                "date": "2026-08-02",
                "description": "Salary",
                "amount": 500.0,
            },
        )


if __name__ == "__main__":
    unittest.main()

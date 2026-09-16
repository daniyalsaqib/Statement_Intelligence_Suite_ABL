import unittest
from datetime import date

from backend.app.models.statement import StatementLine
from backend.app.services.subscription_analysis import (
    detect_recurring_payments,
)


def txn(
    day,
    description,
    debit=None,
    credit=None,
    balance=1000.0,
):
    return StatementLine(
        date=date(2026, 8, day),
        description=description,
        debit=debit,
        credit=credit,
        balance=balance,
    )


class TestRecurringPaymentRegressions(
    unittest.TestCase
):

    def test_empty_statement(self):
        self.assertEqual(
            detect_recurring_payments([]),
            [],
        )

    def test_repeated_debit_candidate(self):
        result = detect_recurring_payments(
            [
                txn(
                    1,
                    "Netflix",
                    debit=100.0,
                ),
                txn(
                    15,
                    "Netflix",
                    debit=100.0,
                ),
            ]
        )

        self.assertEqual(
            len(result),
            1,
        )

        self.assertEqual(
            result[0]["occurrences"],
            2,
        )

    def test_single_debit_not_candidate(self):
        result = detect_recurring_payments(
            [
                txn(
                    1,
                    "Netflix",
                    debit=100.0,
                )
            ]
        )

        self.assertEqual(
            result,
            [],
        )

    def test_credit_repetition_ignored(self):
        result = detect_recurring_payments(
            [
                txn(
                    1,
                    "Salary",
                    credit=1000.0,
                ),
                txn(
                    15,
                    "Salary",
                    credit=1000.0,
                ),
            ]
        )

        self.assertEqual(
            result,
            [],
        )

    def test_case_insensitive_descriptions(self):
        result = detect_recurring_payments(
            [
                txn(
                    1,
                    "Netflix",
                    debit=100.0,
                ),
                txn(
                    15,
                    "NETFLIX",
                    debit=100.0,
                ),
            ]
        )

        self.assertEqual(
            len(result),
            1,
        )

    def test_surrounding_whitespace_normalized(self):
        result = detect_recurring_payments(
            [
                txn(
                    1,
                    "Netflix",
                    debit=100.0,
                ),
                txn(
                    15,
                    "  netflix  ",
                    debit=100.0,
                ),
            ]
        )

        self.assertEqual(
            len(result),
            1,
        )

    def test_internal_whitespace_normalized(self):
        result = detect_recurring_payments(
            [
                txn(
                    1,
                    "PTCL Internet Bill",
                    debit=100.0,
                ),
                txn(
                    15,
                    "PTCL   Internet   Bill",
                    debit=100.0,
                ),
            ]
        )

        self.assertEqual(
            len(result),
            1,
        )

    def test_zero_debits_ignored(self):
        result = detect_recurring_payments(
            [
                txn(
                    1,
                    "Zero Charge",
                    debit=0.0,
                ),
                txn(
                    15,
                    "Zero Charge",
                    debit=0.0,
                ),
            ]
        )

        self.assertEqual(
            result,
            [],
        )

    def test_blank_descriptions_ignored(self):
        result = detect_recurring_payments(
            [
                txn(
                    1,
                    "",
                    debit=100.0,
                ),
                txn(
                    15,
                    "   ",
                    debit=100.0,
                ),
            ]
        )

        self.assertEqual(
            result,
            [],
        )

    def test_amounts_and_dates_preserved(self):
        result = detect_recurring_payments(
            [
                txn(
                    1,
                    "PTCL",
                    debit=3200.0,
                ),
                txn(
                    25,
                    "PTCL",
                    debit=3300.0,
                ),
            ]
        )

        self.assertEqual(
            result[0]["amounts"],
            [
                3200.0,
                3300.0,
            ],
        )

        self.assertEqual(
            result[0]["dates"],
            [
                date(
                    2026,
                    8,
                    1,
                ),
                date(
                    2026,
                    8,
                    25,
                ),
            ],
        )


if __name__ == "__main__":
    unittest.main()

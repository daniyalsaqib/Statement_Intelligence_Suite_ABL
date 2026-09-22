import unittest

from backend.app.services.statement_qa_filter import (
    extract_month_year,
    extract_month_years,
    filter_transactions_by_scopes,
    month_year_label,
    resolve_month_scopes,
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


class TestStatementQAFilterRegressions(unittest.TestCase):

    def test_no_month_reference(self):
        result = resolve_month_scopes(
            "How much did I spend?",
            [
                row(
                    "2026-08-01",
                    "A",
                )
            ],
        )

        self.assertFalse(result.has_month_reference)

        self.assertEqual(
            result.scopes,
            (),
        )

    def test_explicit_month_year(self):
        self.assertEqual(
            extract_month_years("Show August 2026 transactions"),
            [(2026, 8)],
        )

    def test_abbreviated_month_year(self):
        self.assertEqual(
            extract_month_years("Show Aug 2026 transactions"),
            [(2026, 8)],
        )

    def test_sept_alias(self):
        self.assertEqual(
            extract_month_years("Show Sept 2026 transactions"),
            [(2026, 9)],
        )

    def test_shared_year(self):
        self.assertEqual(
            extract_month_years("Compare July and August 2026"),
            [
                (2026, 7),
                (2026, 8),
            ],
        )

    def test_distinct_years(self):
        self.assertEqual(
            extract_month_years(("Compare July 2025 and " "August 2026")),
            [
                (2025, 7),
                (2026, 8),
            ],
        )

    def test_same_month_two_years(self):
        self.assertEqual(
            extract_month_years(("Compare August 2025 and " "August 2026")),
            [
                (2025, 8),
                (2026, 8),
            ],
        )

    def test_duplicate_scope_removed(self):
        self.assertEqual(
            extract_month_years("August 2026 versus Aug 2026"),
            [(2026, 8)],
        )

    def test_modal_may_not_month(self):
        result = resolve_month_scopes(
            "May I see my total spending?",
            [
                row(
                    "2026-08-01",
                    "A",
                )
            ],
        )

        self.assertFalse(result.has_month_reference)

    def test_real_may_month(self):
        result = resolve_month_scopes(
            "How much did I spend in May?",
            [
                row(
                    "2026-05-01",
                    "May",
                )
            ],
        )

        self.assertEqual(
            result.scopes,
            ((2026, 5),),
        )

    def test_multi_scope_filter_preserves_input_order(self):
        data = [
            row(
                "2026-08-02",
                "August B",
            ),
            row(
                "2026-07-01",
                "July",
            ),
            row(
                "2026-09-01",
                "September",
            ),
            row(
                "2026-08-01",
                "August A",
            ),
        ]

        result = filter_transactions_by_scopes(
            data,
            [
                (2026, 7),
                (2026, 8),
            ],
        )

        self.assertEqual(
            [item["description"] for item in result],
            [
                "August B",
                "July",
                "August A",
            ],
        )

    def test_invalid_dates_ignored(self):
        result = filter_transactions_by_scopes(
            [
                row(
                    "not-a-date",
                    "Bad",
                ),
                row(
                    "2026-08-01",
                    "Good",
                ),
            ],
            [(2026, 8)],
        )

        self.assertEqual(
            len(result),
            1,
        )

        self.assertEqual(
            result[0]["description"],
            "Good",
        )

    def test_backward_compatible_first_scope(self):
        self.assertEqual(
            extract_month_year(("Compare July 2026 and " "August 2026")),
            (
                2026,
                7,
            ),
        )

    def test_month_label(self):
        self.assertEqual(
            month_year_label(
                2026,
                8,
            ),
            "August 2026",
        )


if __name__ == "__main__":
    unittest.main()

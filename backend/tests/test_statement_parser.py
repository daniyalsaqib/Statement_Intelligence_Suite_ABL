"""Tests for robust statement CSV parsing."""

from __future__ import annotations

import unittest
from datetime import date
from pathlib import Path

from backend.app.services.statement_parser import (
    StatementParseError,
    parse_statement_csv,
)

SAMPLE_CSV_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "sample_statement.csv"
)


def _parse(text: str, *, encoding: str = "utf-8") -> list:
    return parse_statement_csv(text.encode(encoding))


class StatementParserTests(unittest.TestCase):
    def test_a_sample_csv_unchanged(self):
        content = SAMPLE_CSV_PATH.read_bytes()
        rows = parse_statement_csv(content)

        self.assertEqual(len(rows), 10)
        self.assertEqual(rows[0].date, date(2026, 7, 1))
        self.assertEqual(rows[0].description, "Opening Balance")
        self.assertIsNone(rows[0].debit)
        self.assertIsNone(rows[0].credit)
        self.assertEqual(rows[0].balance, 50000.0)

        self.assertEqual(rows[1].date, date(2026, 7, 2))
        self.assertEqual(rows[1].description, "Netflix")
        self.assertEqual(rows[1].debit, 1500.0)
        self.assertIsNone(rows[1].credit)
        self.assertEqual(rows[1].balance, 48500.0)

        self.assertEqual(rows[2].date, date(2026, 7, 3))
        self.assertEqual(rows[2].description, "Salary")
        self.assertIsNone(rows[2].debit)
        self.assertEqual(rows[2].credit, 80000.0)
        self.assertEqual(rows[2].balance, 128500.0)

        self.assertEqual(rows[-1].date, date(2026, 8, 15))
        self.assertEqual(rows[-1].description, "Grocery Store")
        self.assertEqual(rows[-1].debit, 8000.0)
        self.assertEqual(rows[-1].balance, 178500.0)

    def test_b_capitalized_headers(self):
        csv_text = (
            "Date,Description,Debit,Credit,Balance\n"
            "2026-07-02,Netflix,1500,,48500\n"
        )
        rows = _parse(csv_text)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].description, "Netflix")
        self.assertEqual(rows[0].debit, 1500.0)

    def test_c_headers_with_spaces(self):
        csv_text = (
            " date , description , debit , credit , balance \n"
            "2026-07-02,Netflix,1500,,48500\n"
        )
        rows = _parse(csv_text)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].debit, 1500.0)

    def test_d_utf8_bom(self):
        csv_text = "date,description,debit,credit,balance\n2026-07-02,Netflix,1500,,48500\n"
        rows = parse_statement_csv(csv_text.encode("utf-8-sig"))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].description, "Netflix")

    def test_e_common_header_aliases(self):
        csv_text = (
            "Transaction Date,Description,Debit Amount,Credit Amount,Running Balance\n"
            "2026-07-02,Netflix,1500,,48500\n"
        )
        rows = _parse(csv_text)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].date, date(2026, 7, 2))
        self.assertEqual(rows[0].debit, 1500.0)
        self.assertEqual(rows[0].balance, 48500.0)

    def test_f_comma_thousands(self):
        csv_text = (
            "date,description,debit,credit,balance\n"
            '2026-07-05,Electricity Bill,"12,000",,"116,500"\n'
        )
        rows = _parse(csv_text)
        self.assertEqual(rows[0].debit, 12000.0)
        self.assertEqual(rows[0].balance, 116500.0)

    def test_g_currency_prefixes(self):
        csv_text = (
            "date,description,debit,credit,balance\n"
            '2026-07-02,Netflix,"Rs 1,500",,"Rs. 48500"\n'
            "2026-07-03,Salary,,PKR 80000,PKR128500\n"
            "2026-07-04,ATM,₨500,,$48000\n"
        )
        rows = _parse(csv_text)
        self.assertEqual(rows[0].debit, 1500.0)
        self.assertEqual(rows[0].balance, 48500.0)
        self.assertEqual(rows[1].credit, 80000.0)
        self.assertEqual(rows[2].debit, 500.0)
        self.assertEqual(rows[2].balance, 48000.0)

    def test_h_dd_mm_yyyy_dates(self):
        # Day > 12 makes DD/MM unambiguous; month-name formats are always clear.
        csv_text = (
            "date,description,debit,credit,balance\n"
            "15/07/2026,Netflix,1500,,48500\n"
            "15-08-2026,Grocery,8000,,178500\n"
            "01-Jul-2026,Opening,,,50000\n"
            "03 Jul 2026,Salary,,80000,128500\n"
        )
        rows = _parse(csv_text)
        self.assertEqual(rows[0].date, date(2026, 7, 15))
        self.assertEqual(rows[1].date, date(2026, 8, 15))
        self.assertEqual(rows[2].date, date(2026, 7, 1))
        self.assertEqual(rows[3].date, date(2026, 7, 3))

    def test_i_semicolon_delimited(self):
        csv_text = (
            "date;description;debit;credit;balance\n"
            "2026-07-02;Netflix;1500;;48500\n"
        )
        rows = _parse(csv_text)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].description, "Netflix")
        self.assertEqual(rows[0].debit, 1500.0)

    def test_j_missing_required_column(self):
        csv_text = "date,description,debit,credit\n2026-07-02,Netflix,1500,\n"
        with self.assertRaises(StatementParseError) as ctx:
            _parse(csv_text)
        message = str(ctx.exception)
        self.assertIn("Missing required CSV column: balance", message)
        self.assertIn("Expected columns include: date, description, debit, credit, balance.", message)

    def test_k_invalid_numeric_value(self):
        csv_text = (
            "date,description,debit,credit,balance\n"
            "2026-07-02,Netflix,Rs ABC,,48500\n"
        )
        with self.assertRaises(StatementParseError) as ctx:
            _parse(csv_text)
        self.assertEqual(str(ctx.exception), 'Row 2: invalid debit amount "Rs ABC"')

    def test_l_ambiguous_amount_only_schema_rejected(self):
        csv_text = (
            "date,description,amount,balance\n"
            "2026-07-02,Netflix,1500,48500\n"
        )
        with self.assertRaises(StatementParseError) as ctx:
            _parse(csv_text)
        message = str(ctx.exception)
        self.assertIn("Missing required CSV columns: debit, credit", message)
        self.assertIn(
            "Expected columns include: date, description, debit, credit, balance.",
            message,
        )

    def test_blank_rows_ignored(self):
        csv_text = (
            "date,description,debit,credit,balance\n"
            "2026-07-02,Netflix,1500,,48500\n"
            ",,,,\n"
            "2026-07-03,Salary,,80000,128500\n"
        )
        rows = _parse(csv_text)
        self.assertEqual(len(rows), 2)

    def test_ambiguous_date_rejected(self):
        csv_text = (
            "date,description,debit,credit,balance\n"
            "01/02/2026,Netflix,1500,,48500\n"
        )
        with self.assertRaises(StatementParseError) as ctx:
            _parse(csv_text)
        self.assertIn("ambiguous date", str(ctx.exception))

    def test_unambiguous_us_style_date(self):
        csv_text = (
            "date,description,debit,credit,balance\n"
            "02/13/2026,Netflix,1500,,48500\n"
        )
        rows = _parse(csv_text)
        self.assertEqual(rows[0].date, date(2026, 2, 13))

    def test_parentheses_negative_amount(self):
        csv_text = (
            "date,description,debit,credit,balance\n"
            "2026-07-02,Adjustment,(1500),,48500\n"
        )
        rows = _parse(csv_text)
        self.assertEqual(rows[0].debit, -1500.0)


if __name__ == "__main__":
    unittest.main()

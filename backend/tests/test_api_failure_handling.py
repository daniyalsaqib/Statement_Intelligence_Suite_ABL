import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.statement_parser import (
    StatementParseError,
)


client = TestClient(
    app,
    raise_server_exceptions=False,
)


VALID_CSV = (
    b"date,description,debit,credit,balance\n"
    b"2026-08-01,Test,10,,990\n"
)


class TestAPIFailureHandling(unittest.TestCase):

    # =========================================================
    # STATEMENT UPLOAD
    # =========================================================

    def test_expected_statement_parse_error_remains_400(self):
        with patch(
            "backend.app.routers.statements.parse_statement_csv",
            side_effect=StatementParseError(
                "Missing required CSV column: balance."
            ),
        ):
            response = client.post(
                "/statement/upload",
                files={
                    "file": (
                        "statement.csv",
                        VALID_CSV,
                        "text/csv",
                    )
                },
            )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertIn(
            "Missing required CSV column",
            response.json()["detail"],
        )

    def test_unexpected_parser_failure_returns_safe_500(self):
        secret = (
            "SECRET_INTERNAL_DATABASE_PASSWORD"
        )

        with patch(
            "backend.app.routers.statements.parse_statement_csv",
            side_effect=RuntimeError(
                secret
            ),
        ):
            response = client.post(
                "/statement/upload",
                files={
                    "file": (
                        "statement.csv",
                        VALID_CSV,
                        "text/csv",
                    )
                },
            )

        self.assertEqual(
            response.status_code,
            500,
        )

        body = response.text

        self.assertNotIn(
            secret,
            body,
        )

        self.assertEqual(
            response.json()["detail"],
            (
                "Could not process the uploaded "
                "statement. Please try again."
            ),
        )

    def test_statement_analysis_failure_returns_safe_500(self):
        secret = "SECRET_ANALYSIS_FAILURE"

        with patch(
            "backend.app.routers.statements.analyze_statement",
            side_effect=RuntimeError(
                secret
            ),
        ):
            response = client.post(
                "/statement/upload",
                files={
                    "file": (
                        "statement.csv",
                        VALID_CSV,
                        "text/csv",
                    )
                },
            )

        self.assertEqual(
            response.status_code,
            500,
        )

        self.assertNotIn(
            secret,
            response.text,
        )

        self.assertEqual(
            response.json()["detail"],
            (
                "Could not process the uploaded "
                "statement. Please try again."
            ),
        )

    # =========================================================
    # RECURRING-PAYMENT ANALYSIS
    # =========================================================

    def test_subscription_parse_error_remains_400(self):
        with patch(
            "backend.app.routers.statements.parse_statement_csv",
            side_effect=StatementParseError(
                "Invalid debit amount."
            ),
        ):
            response = client.post(
                "/statement/subscriptions",
                files={
                    "file": (
                        "statement.csv",
                        VALID_CSV,
                        "text/csv",
                    )
                },
            )

        self.assertEqual(
            response.status_code,
            400,
        )

        self.assertIn(
            "Invalid debit amount",
            response.json()["detail"],
        )

    def test_subscription_service_failure_returns_safe_500(self):
        secret = (
            "SECRET_SUBSCRIPTION_FAILURE"
        )

        with patch(
            (
                "backend.app.routers.statements."
                "detect_recurring_payments"
            ),
            side_effect=RuntimeError(
                secret
            ),
        ):
            response = client.post(
                "/statement/subscriptions",
                files={
                    "file": (
                        "statement.csv",
                        VALID_CSV,
                        "text/csv",
                    )
                },
            )

        self.assertEqual(
            response.status_code,
            500,
        )

        self.assertNotIn(
            secret,
            response.text,
        )

        self.assertEqual(
            response.json()["detail"],
            (
                "Could not analyze recurring payments. "
                "Please try again."
            ),
        )

    # =========================================================
    # POLICY RETRIEVAL
    # =========================================================

    def test_policy_retrieval_failure_returns_safe_503(self):
        secret = (
            "postgresql://user:"
            "SUPER_SECRET_PASSWORD@host/database"
        )

        with patch(
            (
                "backend.app.routers.policy_qa."
                "search_policy_documents"
            ),
            side_effect=RuntimeError(
                secret
            ),
        ):
            response = client.post(
                "/policy/ask",
                json={
                    "question": (
                        "What are the available "
                        "public policy details?"
                    ),
                },
            )

        self.assertEqual(
            response.status_code,
            503,
        )

        self.assertNotIn(
            secret,
            response.text,
        )

        self.assertEqual(
            response.json()["detail"],
            (
                "Policy search is temporarily "
                "unavailable. Please try again."
            ),
        )


if __name__ == "__main__":
    unittest.main()

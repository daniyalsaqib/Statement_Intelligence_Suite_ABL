import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.routers.statement_qa import router


# Create a small isolated FastAPI application for Statement Q&A tests.
# This avoids starting the entire project just to test this router.
app = FastAPI()
app.include_router(router)

client = TestClient(app)


class TestStatementQA(unittest.TestCase):

    # ---------------------------------------------------------
    # MONTH / YEAR FILTERING TESTS
    # ---------------------------------------------------------

    @patch("backend.app.routers.statement_qa.ask_llm")
    def test_month_year_query_with_matching_rows(self, mock_gemini):
        mock_gemini.return_value = "July 2025 transaction summary."

        payload = {
            "question": "Tell me about July 2025 transactions",
            "statement_data": [
                {
                    "date": "2025-07-05",
                    "description": "July Purchase",
                    "debit": 100.0,
                    "credit": None,
                    "balance": 900.0,
                },
                {
                    "date": "2025-08-05",
                    "description": "August Purchase",
                    "debit": 200.0,
                    "credit": None,
                    "balance": 700.0,
                },
            ],
        }

        response = client.post("/statement/ask", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["answer"],
            "July 2025 transaction summary.",
        )

        mock_gemini.assert_called_once()

    @patch("backend.app.routers.statement_qa.ask_llm")
    def test_month_year_query_with_no_matching_rows(self, mock_gemini):
        payload = {
            "question": "Tell me about July 2025 transactions",
            "statement_data": [
                {
                    "date": "2026-08-01",
                    "description": "Purchase",
                    "debit": 100.0,
                    "credit": None,
                    "balance": 900.0,
                }
            ],
        }

        response = client.post("/statement/ask", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["answer"],
            "No transactions found for July 2025.",
        )

        mock_gemini.assert_not_called()

    @patch("backend.app.routers.statement_qa.ask_llm")
    def test_month_detection_is_case_insensitive(self, mock_gemini):
        mock_gemini.return_value = "July summary."

        payload = {
            "question": "Tell me about JULY 2025 transactions",
            "statement_data": [
                {
                    "date": "2025-07-10",
                    "description": "Purchase",
                    "debit": 50.0,
                    "credit": None,
                    "balance": 950.0,
                }
            ],
        }

        response = client.post("/statement/ask", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["answer"],
            "July summary.",
        )

        mock_gemini.assert_called_once()

    @patch("backend.app.routers.statement_qa.ask_llm")
    def test_abbreviated_month_is_supported(self, mock_gemini):
        mock_gemini.return_value = "July summary."

        payload = {
            "question": "Tell me about Jul 2025 transactions",
            "statement_data": [
                {
                    "date": "2025-07-15",
                    "description": "Purchase",
                    "debit": 75.0,
                    "credit": None,
                    "balance": 925.0,
                }
            ],
        }

        response = client.post("/statement/ask", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["answer"],
            "July summary.",
        )

        mock_gemini.assert_called_once()

    @patch("backend.app.routers.statement_qa.ask_llm")
    def test_non_month_question_still_uses_normal_flow(
        self,
        mock_gemini,
    ):
        mock_gemini.return_value = "Normal statement answer."

        payload = {
            "question": "Summarize my spending patterns",
            "statement_data": [
                {
                    "date": "2026-08-01",
                    "description": "Purchase",
                    "debit": 100.0,
                    "credit": None,
                    "balance": 900.0,
                }
            ],
        }

        response = client.post("/statement/ask", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["answer"],
            "Normal statement answer.",
        )

        mock_gemini.assert_called_once()

    @patch("backend.app.routers.statement_qa.ask_llm")
    def test_only_matching_month_rows_are_sent_to_gemini(
        self,
        mock_gemini,
    ):
        mock_gemini.return_value = "August summary."

        payload = {
            "question": "Tell me about August 2026 transactions",
            "statement_data": [
                {
                    "date": "2026-08-01",
                    "description": "August Purchase",
                    "debit": 100.0,
                    "credit": None,
                    "balance": 900.0,
                },
                {
                    "date": "2026-07-01",
                    "description": "July Purchase",
                    "debit": 900.0,
                    "credit": None,
                    "balance": 1800.0,
                },
            ],
        }

        response = client.post("/statement/ask", json=payload)

        self.assertEqual(response.status_code, 200)

        mock_gemini.assert_called_once()

        prompt = mock_gemini.call_args.args[0]

        self.assertIn("August Purchase", prompt)
        self.assertNotIn("July Purchase", prompt)

    @patch("backend.app.routers.statement_qa.ask_llm")
    def test_gemini_exception_is_handled(self, mock_gemini):
        mock_gemini.side_effect = RuntimeError("Provider failure")

        payload = {
            "question": "Summarize my spending patterns",
            "statement_data": [
                {
                    "date": "2026-08-01",
                    "description": "Purchase",
                    "debit": 100.0,
                    "credit": None,
                    "balance": 900.0,
                }
            ],
        }

        response = client.post("/statement/ask", json=payload)

        self.assertEqual(response.status_code, 502)
        self.assertEqual(
            response.json()["detail"],
            (
                "Could not generate an answer from the statement agent. "
                "Please try again."
            ),
        )

    @patch("backend.app.routers.statement_qa.ask_llm")
    def test_empty_gemini_output_is_handled(self, mock_gemini):
        mock_gemini.return_value = "   "

        payload = {
            "question": "Summarize unusual transactions",
            "statement_data": [
                {
                    "date": "2026-08-01",
                    "description": "Purchase",
                    "debit": 100.0,
                    "credit": None,
                    "balance": 900.0,
                }
            ],
        }

        response = client.post("/statement/ask", json=payload)

        self.assertEqual(response.status_code, 502)
        self.assertEqual(
            response.json()["detail"],
            (
                "Could not generate an answer from the statement agent. "
                "Please try again."
            ),
        )

    # ---------------------------------------------------------
    # DETERMINISTIC Q&A TESTS
    # ---------------------------------------------------------

    @patch("backend.app.routers.statement_qa.ask_llm")
    def test_deterministic_transaction_count(self, mock_gemini):
        payload = {
            "question": "How many transactions are in this statement?",
            "statement_data": [
                {
                    "date": "2026-08-01",
                    "description": "A",
                    "debit": 100.0,
                    "credit": None,
                    "balance": 900.0,
                },
                {
                    "date": "2026-08-02",
                    "description": "B",
                    "debit": None,
                    "credit": 200.0,
                    "balance": 1100.0,
                },
            ],
        }

        response = client.post("/statement/ask", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["answer"],
            "This statement contains 2 transactions.",
        )

        mock_gemini.assert_not_called()

    @patch("backend.app.routers.statement_qa.ask_llm")
    def test_deterministic_total_spending(self, mock_gemini):
        payload = {
            "question": "How much did I spend?",
            "statement_data": [
                {
                    "date": "2026-08-01",
                    "description": "Purchase A",
                    "debit": 100.0,
                    "credit": None,
                    "balance": 900.0,
                },
                {
                    "date": "2026-08-02",
                    "description": "Purchase B",
                    "debit": 50.0,
                    "credit": None,
                    "balance": 850.0,
                },
            ],
        }

        response = client.post("/statement/ask", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["answer"],
            "Your total spending is 150.00.",
        )

        mock_gemini.assert_not_called()

    @patch("backend.app.routers.statement_qa.ask_llm")
    def test_deterministic_closing_balance(self, mock_gemini):
        payload = {
            "question": "What is my closing balance?",
            "statement_data": [
                {
                    "date": "2026-08-01",
                    "description": "A",
                    "debit": None,
                    "credit": None,
                    "balance": 1000.0,
                },
                {
                    "date": "2026-08-02",
                    "description": "B",
                    "debit": None,
                    "credit": None,
                    "balance": 1250.0,
                },
            ],
        }

        response = client.post("/statement/ask", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["answer"],
            "Your closing balance is 1,250.00.",
        )

        mock_gemini.assert_not_called()

    @patch("backend.app.routers.statement_qa.ask_llm")
    def test_deterministic_largest_debit(self, mock_gemini):
        payload = {
            "question": "What is my largest debit transaction?",
            "statement_data": [
                {
                    "date": "2026-08-01",
                    "description": "Small Purchase",
                    "debit": 100.0,
                    "credit": None,
                    "balance": 900.0,
                },
                {
                    "date": "2026-08-02",
                    "description": "Large Purchase",
                    "debit": 500.0,
                    "credit": None,
                    "balance": 400.0,
                },
            ],
        }

        response = client.post("/statement/ask", json=payload)

        self.assertEqual(response.status_code, 200)

        answer = response.json()["answer"]

        self.assertIn("500.00", answer)
        self.assertIn("Large Purchase", answer)
        self.assertIn("2026-08-02", answer)

        mock_gemini.assert_not_called()

    # ---------------------------------------------------------
    # MONTH-SPECIFIC DETERMINISTIC Q&A
    # ---------------------------------------------------------

    @patch("backend.app.routers.statement_qa.ask_llm")
    def test_month_specific_spending_is_deterministic_and_filtered(
        self,
        mock_gemini,
    ):
        payload = {
            "question": "How much did I spend in August 2026?",
            "statement_data": [
                {
                    "date": "2026-08-01",
                    "description": "August Purchase",
                    "debit": 100.0,
                    "credit": None,
                    "balance": 900.0,
                },
                {
                    "date": "2026-07-01",
                    "description": "July Purchase",
                    "debit": 900.0,
                    "credit": None,
                    "balance": 1800.0,
                },
            ],
        }

        response = client.post("/statement/ask", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["answer"],
            "Your total spending is 100.00.",
        )

        mock_gemini.assert_not_called()


if __name__ == "__main__":
    unittest.main()

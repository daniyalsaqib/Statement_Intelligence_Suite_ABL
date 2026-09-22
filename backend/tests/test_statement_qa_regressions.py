import unittest

from unittest.mock import patch


from fastapi import FastAPI

from fastapi.testclient import TestClient


from backend.app.routers.statement_qa import router

app = FastAPI()

app.include_router(router)


client = TestClient(app)


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


class TestStatementQARegressions(unittest.TestCase):

    def _post(
        self,
        question,
        statement_data,
        llm_output="Qualitative summary.",
        conversation_history=None,
    ):
        patcher = patch("backend.app.routers.statement_qa.ask_llm")

        mock_llm = patcher.start()
        self.addCleanup(patcher.stop)

        mock_llm.return_value = llm_output

        payload = {
            "question": question,
            "statement_data": statement_data,
        }

        # MULTI-TURN TEST SUPPORT:
        #
        # Purane one-shot tests history nahi bhejte,
        # isliye existing tests bilkul waise hi kaam karte rahenge.
        #
        # Sirf conversational tests ke liye hum optional
        # conversation_history request mein add karte hain.
        if conversation_history is not None:
            payload["conversation_history"] = conversation_history

        response = client.post(
            "/statement/ask",
            json=payload,
        )

        return response, mock_llm

        # =========================================================

    # NATURAL FINANCIAL LANGUAGE TRUST BOUNDARY
    # =========================================================
    #
    # PURPOSE:
    # Users banking questions hamesha exact developer wording
    # mein nahi poochte.
    #
    # "spending", "expenditure", "outflow", aur
    # "money went out" same underlying financial intent
    # represent kar sakte hain.
    #
    # In tests ka main security goal ye verify karna hai ke
    # known financial synonyms deterministic Python path use
    # karein instead of letting the LLM invent/recalculate
    # financial amounts.

    def test_expenditure_phrase_is_deterministic(
        self,
    ):
        response, mock_llm = self._post(
            "What was my expenditure?",
            [
                row(
                    "2026-08-01",
                    "Purchase A",
                    debit=100.0,
                    balance=900.0,
                ),
                row(
                    "2026-08-02",
                    "Purchase B",
                    debit=50.0,
                    balance=850.0,
                ),
            ],
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        # Verified Python calculation:
        # 100 + 50 = 150.
        self.assertIn(
            "150.00",
            response.json()["answer"],
        )

        # Known financial totals should not require Groq.
        mock_llm.assert_not_called()

    def test_money_went_out_phrase_is_deterministic(
        self,
    ):
        response, mock_llm = self._post(
            "How much money went out?",
            [
                row(
                    "2026-08-01",
                    "Purchase A",
                    debit=80.0,
                    balance=920.0,
                ),
                row(
                    "2026-08-02",
                    "Purchase B",
                    debit=20.0,
                    balance=900.0,
                ),
            ],
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        # Verified Python calculation:
        # 80 + 20 = 100.
        self.assertIn(
            "100.00",
            response.json()["answer"],
        )

        mock_llm.assert_not_called()

    def test_expenditure_compound_question_uses_verified_figures(
        self,
    ):
        # PURPOSE:
        # Natural synonym + multiple requested financial facts
        # open-ended/compound path ko exercise karte hain.
        #
        # Agar LLM wrong numeric values generate bhi kare,
        # backend verified Python figures ko authoritative
        # rakhna chahiye.

        response, mock_llm = self._post(
            ("What was my total expenditure and " "what was my closing balance?"),
            [
                row(
                    "2026-08-01",
                    "Purchase A",
                    debit=100.0,
                    balance=900.0,
                ),
                row(
                    "2026-08-02",
                    "Purchase B",
                    debit=50.0,
                    balance=850.0,
                ),
            ],
            llm_output=(
                "Your expenditure was 999999.00 and "
                "your closing balance was 888888.00."
            ),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        answer = response.json()["answer"]

        # Verified debit total:
        # 100 + 50 = 150.
        self.assertIn(
            "Total spending: 150.00.",
            answer,
        )

        # Verified final statement balance.
        self.assertIn(
            "Closing balance: 850.00.",
            answer,
        )

        # Deliberately incorrect LLM-generated financial
        # figures must never reach the final response.
        self.assertNotIn(
            "999999.00",
            answer,
        )

        self.assertNotIn(
            "888888.00",
            answer,
        )

        # Compound qualitative path may still consult the LLM,
        # but its numeric output remains subordinate to
        # deterministic backend facts.
        mock_llm.assert_called_once()

    def test_outflows_phrase_is_deterministic(
        self,
    ):
        response, mock_llm = self._post(
            "What were my outflows?",
            [
                row(
                    "2026-08-01",
                    "Purchase",
                    debit=75.0,
                    balance=925.0,
                ),
            ],
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        # "Outflows" must resolve to verified debits.
        self.assertIn(
            "75.00",
            response.json()["answer"],
        )

        mock_llm.assert_not_called()

    def test_money_came_in_phrase_is_deterministic(
        self,
    ):
        response, mock_llm = self._post(
            "How much money came in?",
            [
                row(
                    "2026-08-01",
                    "Salary",
                    credit=5000.0,
                    balance=5000.0,
                ),
                row(
                    "2026-08-02",
                    "Refund",
                    credit=250.0,
                    balance=5250.0,
                ),
            ],
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        # Verified Python calculation:
        # 5000 + 250 = 5250.
        self.assertIn(
            "5,250.00",
            response.json()["answer"],
        )

        # Incoming-money synonyms must also stay deterministic.
        mock_llm.assert_not_called()

    # =========================================================
    # MULTI-TURN STATEMENT FOLLOW-UPS
    # =========================================================

    def test_follow_up_reuses_previous_user_intent_for_new_month(
        self,
    ):
        statement_data = [
            row(
                "2026-07-01",
                "July Purchase A",
                debit=40.0,
                balance=960.0,
            ),
            row(
                "2026-07-02",
                "July Purchase B",
                debit=30.0,
                balance=930.0,
            ),
            row(
                "2026-08-01",
                "August Purchase",
                debit=200.0,
                balance=730.0,
            ),
        ]

        response, mock_llm = self._post(
            "What about July?",
            statement_data,
            conversation_history=[
                {
                    "role": "user",
                    "content": ("How much did I spend in August?"),
                },
                {
                    "role": "assistant",
                    "content": ("You spent 999999.00 in August."),
                },
            ],
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        answer = response.json()["answer"]

        # July spending = 40 + 30 = 70.
        #
        # Backend ko previous USER intent samajhna hai,
        # lekin amount current July rows se dobara
        # deterministic Python se calculate karna hai.
        self.assertIn(
            "70.00",
            answer,
        )

        # August ka amount current answer mein use nahi hona chahiye.
        self.assertNotIn(
            "200.00",
            answer,
        )

        # Previous assistant ne jaan boojh kar wrong amount diya.
        # Backend us assistant answer ko financial truth nahi
        # samajh sakta.
        self.assertNotIn(
            "999999.00",
            answer,
        )

        # Is simple spending follow-up ke liye Groq ki
        # zarurat nahi honi chahiye.
        mock_llm.assert_not_called()

    def test_chained_follow_up_keeps_original_user_intent(
        self,
    ):
        statement_data = [
            row(
                "2026-06-01",
                "June Purchase",
                debit=25.0,
                balance=975.0,
            ),
            row(
                "2026-07-01",
                "July Purchase",
                debit=50.0,
                balance=925.0,
            ),
            row(
                "2026-08-01",
                "August Purchase",
                debit=100.0,
                balance=825.0,
            ),
        ]

        response, mock_llm = self._post(
            "What about June?",
            statement_data,
            conversation_history=[
                {
                    "role": "user",
                    "content": ("How much did I spend in August?"),
                },
                {
                    "role": "assistant",
                    "content": "Previous August answer.",
                },
                {
                    "role": "user",
                    "content": "What about July?",
                },
                {
                    "role": "assistant",
                    "content": "Previous July answer.",
                },
            ],
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        answer = response.json()["answer"]

        # "What about July?" khud complete financial
        # intent nahi hai.
        #
        # Helper ko us follow-up ko skip karke original
        # user intent recover karna chahiye:
        #
        # "How much did I spend in August?"
        #
        # Phir current June rows par wohi spending intent
        # deterministically apply hoga.
        self.assertIn(
            "25.00",
            answer,
        )

        self.assertNotIn(
            "50.00",
            answer,
        )

        self.assertNotIn(
            "100.00",
            answer,
        )

        mock_llm.assert_not_called()

    def test_follow_up_skips_unrelated_capability_question(
        self,
    ):
        # PURPOSE:
        # Unified assistant history can contain messages from
        # different internal capabilities.
        #
        # A recurring-payment question between two statement
        # questions must not replace the reusable financial
        # intent for a later scope-only follow-up.

        statement_data = [
            row(
                "2026-07-01",
                "July Purchase A",
                debit=40.0,
                balance=960.0,
            ),
            row(
                "2026-07-02",
                "July Purchase B",
                debit=30.0,
                balance=930.0,
            ),
            row(
                "2026-08-01",
                "August Purchase",
                debit=200.0,
                balance=730.0,
            ),
        ]

        response, mock_llm = self._post(
            "What about July?",
            statement_data,
            conversation_history=[
                {
                    "role": "user",
                    "content": "How much did I spend in August?",
                },
                {
                    "role": "assistant",
                    "content": "Previous verified August answer.",
                },
                {
                    "role": "user",
                    "content": "Which payments keep repeating?",
                },
                {
                    "role": "assistant",
                    "content": "Recurring-payment answer.",
                },
            ],
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        answer = response.json()["answer"]

        # July spending = 40 + 30 = 70.
        #
        # Backend intervening recurring question ko skip
        # karke earlier spending intent reuse karega.
        self.assertIn(
            "70.00",
            answer,
        )

        # August amount July answer mein leak nahi hona chahiye.
        self.assertNotIn(
            "200.00",
            answer,
        )

        # Financial answer deterministic Python se aata hai.
        # Is follow-up ke liye Groq call nahi honi chahiye.
        mock_llm.assert_not_called()

    # =========================================================

    # VERIFIED COMPOUND FINANCIAL QUESTIONS

    # =========================================================

    def test_compound_spending_and_closing_balance(self):

        response, mock_llm = self._post(
            ("How much did I spend and " "what was my closing balance?"),
            [
                row(
                    "2026-08-01",
                    "Purchase A",
                    debit=100.0,
                    balance=900.0,
                ),
                row(
                    "2026-08-02",
                    "Purchase B",
                    debit=50.0,
                    balance=850.0,
                ),
            ],
            ("You spent 999.00 and your " "closing balance is 888.00."),
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        answer = response.json()["answer"]

        self.assertIn(
            "Total spending: 150.00.",
            answer,
        )

        self.assertIn(
            "Closing balance: 850.00.",
            answer,
        )

        self.assertNotIn(
            "999.00",
            answer,
        )

        self.assertNotIn(
            "888.00",
            answer,
        )

        mock_llm.assert_called_once()

    def test_compound_opening_and_closing_balance(self):

        response, mock_llm = self._post(
            ("What were my opening balance " "and closing balance?"),
            [
                row(
                    "2026-08-01",
                    "Opening",
                    balance=1000.0,
                ),
                row(
                    "2026-08-02",
                    "Purchase",
                    debit=100.0,
                    balance=900.0,
                ),
            ],
            "Opening was 5 and closing was 6.",
        )

        answer = response.json()["answer"]

        self.assertIn(
            "Opening balance: 1,000.00.",
            answer,
        )

        self.assertIn(
            "Closing balance: 900.00.",
            answer,
        )

        self.assertNotIn(
            "Opening was 5",
            answer,
        )

        mock_llm.assert_called_once()

    def test_compound_total_credit_and_closing_balance(self):

        response, mock_llm = self._post(
            ("How much did I receive and " "what was my closing balance?"),
            [
                row(
                    "2026-08-01",
                    "Salary",
                    credit=800.0,
                    balance=800.0,
                ),
                row(
                    "2026-08-02",
                    "Purchase",
                    debit=100.0,
                    balance=700.0,
                ),
            ],
            ("You received 999.00 and " "closed at 888.00."),
        )

        answer = response.json()["answer"]

        self.assertIn(
            "Total credits: 800.00.",
            answer,
        )

        self.assertIn(
            "Closing balance: 700.00.",
            answer,
        )

        self.assertNotIn(
            "999.00",
            answer,
        )

        self.assertNotIn(
            "888.00",
            answer,
        )

        mock_llm.assert_called_once()

    def test_compound_transaction_count_is_verified(self):

        response, mock_llm = self._post(
            ("How many transactions are there " "and what stands out?"),
            [
                row(
                    "2026-08-01",
                    "A",
                    debit=10.0,
                    balance=990.0,
                ),
                row(
                    "2026-08-02",
                    "B",
                    credit=20.0,
                    balance=1010.0,
                ),
            ],
            "There are 999 transactions.",
        )

        answer = response.json()["answer"]

        self.assertIn(
            "Transaction count: 2.",
            answer,
        )

        self.assertNotIn(
            "999",
            answer,
        )

        mock_llm.assert_called_once()

    def test_compound_debit_credit_counts_are_verified(self):

        response, mock_llm = self._post(
            ("How many debit transactions and " "credit transactions are there?"),
            [
                row(
                    "2026-08-01",
                    "Debit A",
                    debit=10.0,
                    balance=990.0,
                ),
                row(
                    "2026-08-02",
                    "Credit",
                    credit=20.0,
                    balance=1010.0,
                ),
                row(
                    "2026-08-03",
                    "Debit B",
                    debit=30.0,
                    balance=980.0,
                ),
            ],
            "There are 99 debits and 88 credits.",
        )

        answer = response.json()["answer"]

        self.assertIn(
            "Debit transaction count: 2.",
            answer,
        )

        self.assertIn(
            "Credit transaction count: 1.",
            answer,
        )

        self.assertNotIn(
            "99",
            answer,
        )

        self.assertNotIn(
            "88",
            answer,
        )

        mock_llm.assert_called_once()

    def test_compound_largest_debit_is_verified(self):

        response, mock_llm = self._post(
            ("What was my largest debit " "and what stands out?"),
            [
                row(
                    "2026-08-01",
                    "Small Purchase",
                    debit=100.0,
                    balance=900.0,
                ),
                row(
                    "2026-08-02",
                    "Large Purchase",
                    debit=500.0,
                    balance=400.0,
                ),
            ],
            "The largest debit was 999.00.",
        )

        answer = response.json()["answer"]

        self.assertIn(
            "Largest debit:",
            answer,
        )

        self.assertIn(
            "500.00",
            answer,
        )

        self.assertIn(
            "2026-08-02",
            answer,
        )

        self.assertIn(
            "Large Purchase",
            answer,
        )

        self.assertNotIn(
            "999.00",
            answer,
        )

        mock_llm.assert_called_once()

    def test_compound_largest_credit_is_verified(self):

        response, mock_llm = self._post(
            ("What was my largest credit " "and explain it?"),
            [
                row(
                    "2026-08-01",
                    "Small Credit",
                    credit=100.0,
                    balance=100.0,
                ),
                row(
                    "2026-08-03",
                    "Salary",
                    credit=800.0,
                    balance=900.0,
                ),
            ],
            "The largest credit was 999.00.",
        )

        answer = response.json()["answer"]

        self.assertIn(
            "Largest credit:",
            answer,
        )

        self.assertIn(
            "800.00",
            answer,
        )

        self.assertIn(
            "2026-08-03",
            answer,
        )

        self.assertIn(
            "Salary",
            answer,
        )

        self.assertNotIn(
            "999.00",
            answer,
        )

        mock_llm.assert_called_once()

    def test_compound_credit_then_debit_counts_are_verified(self):

        response, mock_llm = self._post(
            ("How many credit transactions and " "debit transactions are there?"),
            [
                row(
                    "2026-08-01",
                    "Debit A",
                    debit=10.0,
                    balance=990.0,
                ),
                row(
                    "2026-08-02",
                    "Credit",
                    credit=20.0,
                    balance=1010.0,
                ),
                row(
                    "2026-08-03",
                    "Debit B",
                    debit=30.0,
                    balance=980.0,
                ),
            ],
            "There are 99 credits and 88 debits.",
        )

        answer = response.json()["answer"]

        self.assertIn(
            "Credit transaction count: 1.",
            answer,
        )

        self.assertIn(
            "Debit transaction count: 2.",
            answer,
        )

        self.assertNotIn(
            "99",
            answer,
        )

        self.assertNotIn(
            "88",
            answer,
        )

        mock_llm.assert_called_once()

    def test_compound_shared_noun_debit_credit_counts_are_verified(self):

        response, mock_llm = self._post(
            ("How many debit and credit " "transactions are there?"),
            [
                row(
                    "2026-08-01",
                    "Debit A",
                    debit=10.0,
                    balance=990.0,
                ),
                row(
                    "2026-08-02",
                    "Credit",
                    credit=20.0,
                    balance=1010.0,
                ),
                row(
                    "2026-08-03",
                    "Debit B",
                    debit=30.0,
                    balance=980.0,
                ),
            ],
            "There are 99 transactions.",
        )

        answer = response.json()["answer"]

        self.assertIn(
            "Debit transaction count: 2.",
            answer,
        )

        self.assertIn(
            "Credit transaction count: 1.",
            answer,
        )

        self.assertNotIn(
            "99",
            answer,
        )

        mock_llm.assert_called_once()

    # =========================================================

    # NUMERIC GUARD

    # =========================================================

    def test_safe_qualitative_commentary_is_preserved(self):

        response, _ = self._post(
            ("How much did I spend " "and what stands out?"),
            [
                row(
                    "2026-08-01",
                    "A",
                    debit=100.0,
                    balance=900.0,
                ),
                row(
                    "2026-08-02",
                    "B",
                    debit=50.0,
                    balance=850.0,
                ),
            ],
            ("Spending is concentrated in " "a small set of transactions."),
        )

        answer = response.json()["answer"]

        self.assertIn(
            "Total spending: 150.00.",
            answer,
        )

        self.assertIn(
            ("Spending is concentrated in " "a small set of transactions."),
            answer,
        )

    def test_llm_digits_are_discarded(self):

        response, _ = self._post(
            ("How much did I spend " "and what stands out?"),
            [
                row(
                    "2026-08-01",
                    "A",
                    debit=100.0,
                    balance=900.0,
                )
            ],
            "A suspicious amount is 999.",
        )

        answer = response.json()["answer"]

        self.assertIn(
            "Total spending: 100.00.",
            answer,
        )

        self.assertNotIn(
            "999",
            answer,
        )

    def test_llm_currency_word_is_discarded(self):

        response, _ = self._post(
            ("How much did I spend " "and what stands out?"),
            [
                row(
                    "2026-08-01",
                    "A",
                    debit=100.0,
                    balance=900.0,
                )
            ],
            "The spending is notable in PKR terms.",
        )

        self.assertNotIn(
            "PKR",
            response.json()["answer"],
        )

    def test_llm_currency_symbol_is_discarded(self):

        response, _ = self._post(
            ("How much did I spend " "and what stands out?"),
            [
                row(
                    "2026-08-01",
                    "A",
                    debit=100.0,
                    balance=900.0,
                )
            ],
            "The pattern is notable in $ terms.",
        )

        self.assertNotIn(
            "$",
            response.json()["answer"],
        )

    # =========================================================

    # COMPOUND QUESTION CLASSIFICATION

    # =========================================================

    def test_ampersand_compound_question(self):

        response, mock_llm = self._post(
            ("How much did I spend & " "what was my closing balance?"),
            [
                row(
                    "2026-08-01",
                    "A",
                    debit=100.0,
                    balance=900.0,
                ),
                row(
                    "2026-08-02",
                    "B",
                    debit=50.0,
                    balance=850.0,
                ),
            ],
            "Wrong 999.",
        )

        answer = response.json()["answer"]

        self.assertIn(
            "Total spending: 150.00.",
            answer,
        )

        self.assertIn(
            "Closing balance: 850.00.",
            answer,
        )

        mock_llm.assert_called_once()

    def test_multi_sentence_compound_question(self):

        response, mock_llm = self._post(
            ("How much did I spend? " "What was my closing balance?"),
            [
                row(
                    "2026-08-01",
                    "A",
                    debit=100.0,
                    balance=900.0,
                ),
                row(
                    "2026-08-02",
                    "B",
                    debit=50.0,
                    balance=850.0,
                ),
            ],
            "Wrong 999.",
        )

        answer = response.json()["answer"]

        self.assertIn(
            "Total spending: 150.00.",
            answer,
        )

        self.assertIn(
            "Closing balance: 850.00.",
            answer,
        )

        mock_llm.assert_called_once()

    def test_comma_compound_question(self):

        response, mock_llm = self._post(
            ("How much did I spend, " "what was my closing balance?"),
            [
                row(
                    "2026-08-01",
                    "A",
                    debit=100.0,
                    balance=900.0,
                ),
                row(
                    "2026-08-02",
                    "B",
                    debit=50.0,
                    balance=850.0,
                ),
            ],
            "Wrong 999.",
        )

        answer = response.json()["answer"]

        self.assertIn(
            "Total spending: 150.00.",
            answer,
        )

        self.assertIn(
            "Closing balance: 850.00.",
            answer,
        )

        mock_llm.assert_called_once()

    # =========================================================

    # MONTH RESOLUTION

    # =========================================================

    def test_unique_month_without_year(self):

        response, mock_llm = self._post(
            "How much did I spend in August?",
            [
                row(
                    "2026-07-05",
                    "July Purchase",
                    debit=900.0,
                    balance=1100.0,
                ),
                row(
                    "2026-08-05",
                    "August Purchase",
                    debit=100.0,
                    balance=1000.0,
                ),
            ],
        )

        self.assertEqual(
            response.json()["answer"],
            "Your total spending is 100.00.",
        )

        mock_llm.assert_not_called()

    def test_ambiguous_month_without_year(self):

        response, mock_llm = self._post(
            "How much did I spend in August?",
            [
                row(
                    "2025-08-05",
                    "Old",
                    debit=200.0,
                    balance=800.0,
                ),
                row(
                    "2026-08-05",
                    "New",
                    debit=100.0,
                    balance=700.0,
                ),
            ],
        )

        self.assertEqual(
            response.json()["answer"],
            (
                "Multiple August periods were found. "
                "Please include the year in your question."
            ),
        )

        mock_llm.assert_not_called()

    def test_missing_month_without_year(self):

        response, mock_llm = self._post(
            "How much did I spend in September?",
            [
                row(
                    "2026-08-01",
                    "A",
                    debit=100.0,
                    balance=900.0,
                )
            ],
        )

        self.assertEqual(
            response.json()["answer"],
            "No transactions found for September.",
        )

        mock_llm.assert_not_called()

    def test_missing_explicit_month_year(self):

        response, mock_llm = self._post(
            "How much did I spend in September 2026?",
            [
                row(
                    "2026-08-01",
                    "A",
                    debit=100.0,
                    balance=900.0,
                )
            ],
        )

        self.assertEqual(
            response.json()["answer"],
            "No transactions found for September 2026.",
        )

        mock_llm.assert_not_called()

    def test_aug_abbreviation_without_year(self):

        response, mock_llm = self._post(
            "How much did I spend in Aug?",
            [
                row(
                    "2026-07-01",
                    "July",
                    debit=900.0,
                    balance=1100.0,
                ),
                row(
                    "2026-08-01",
                    "August",
                    debit=100.0,
                    balance=1000.0,
                ),
            ],
        )

        self.assertEqual(
            response.json()["answer"],
            "Your total spending is 100.00.",
        )

        mock_llm.assert_not_called()

    def test_month_detection_case_insensitive(self):

        response, mock_llm = self._post(
            "HOW MUCH DID I SPEND IN AUGUST?",
            [
                row(
                    "2026-07-01",
                    "July",
                    debit=900.0,
                    balance=1100.0,
                ),
                row(
                    "2026-08-01",
                    "August",
                    debit=100.0,
                    balance=1000.0,
                ),
            ],
        )

        self.assertEqual(
            response.json()["answer"],
            "Your total spending is 100.00.",
        )

        mock_llm.assert_not_called()

    def test_modal_may_is_not_month(self):

        response, mock_llm = self._post(
            "May I see my total spending?",
            [
                row(
                    "2026-07-01",
                    "July",
                    debit=900.0,
                    balance=1100.0,
                ),
                row(
                    "2026-08-01",
                    "August",
                    debit=100.0,
                    balance=1000.0,
                ),
            ],
        )

        self.assertEqual(
            response.json()["answer"],
            "Your total spending is 1,000.00.",
        )

        mock_llm.assert_not_called()

    def test_actual_may_reference(self):

        response, mock_llm = self._post(
            "How much did I spend in May?",
            [
                row(
                    "2026-05-01",
                    "May Purchase",
                    debit=100.0,
                    balance=900.0,
                ),
                row(
                    "2026-06-01",
                    "June Purchase",
                    debit=300.0,
                    balance=600.0,
                ),
            ],
        )

        self.assertEqual(
            response.json()["answer"],
            "Your total spending is 100.00.",
        )

        mock_llm.assert_not_called()

    # =========================================================

    # MULTI-MONTH COMPARISONS

    # =========================================================

    def test_explicit_multi_month_comparison(self):

        response, mock_llm = self._post(
            ("Compare July 2026 and " "August 2026 spending."),
            [
                row(
                    "2026-07-05",
                    "July Purchase",
                    debit=900.0,
                    balance=1100.0,
                ),
                row(
                    "2026-08-05",
                    "August Purchase",
                    debit=100.0,
                    balance=1000.0,
                ),
            ],
            "Spending was higher in July.",
        )

        answer = response.json()["answer"]

        self.assertIn(
            "July 2026 spending: 900.00.",
            answer,
        )

        self.assertIn(
            "August 2026 spending: 100.00.",
            answer,
        )

        self.assertIn(
            ("July 2026 spending was higher " "than August 2026 spending."),
            answer,
        )

        mock_llm.assert_called_once()

    def test_shared_year_multi_month_comparison(self):

        response, _ = self._post(
            "Compare July and August 2026 spending.",
            [
                row(
                    "2026-07-05",
                    "July",
                    debit=900.0,
                    balance=1100.0,
                ),
                row(
                    "2026-08-05",
                    "August",
                    debit=100.0,
                    balance=1000.0,
                ),
            ],
            "July was higher.",
        )

        answer = response.json()["answer"]

        self.assertIn(
            "July 2026 spending: 900.00.",
            answer,
        )

        self.assertIn(
            "August 2026 spending: 100.00.",
            answer,
        )

    def test_cross_year_comparison(self):

        response, _ = self._post(
            ("Compare July 2025 and " "August 2026 spending."),
            [
                row(
                    "2025-07-01",
                    "Old",
                    debit=900.0,
                    balance=100.0,
                ),
                row(
                    "2026-08-01",
                    "New",
                    debit=100.0,
                    balance=900.0,
                ),
            ],
            "July was higher.",
        )

        answer = response.json()["answer"]

        self.assertIn(
            "July 2025 spending: 900.00.",
            answer,
        )

        self.assertIn(
            "August 2026 spending: 100.00.",
            answer,
        )

    def test_same_month_across_two_years(self):

        response, _ = self._post(
            ("Compare August 2025 and " "August 2026 spending."),
            [
                row(
                    "2025-08-01",
                    "Old",
                    debit=200.0,
                    balance=800.0,
                ),
                row(
                    "2026-08-01",
                    "New",
                    debit=100.0,
                    balance=700.0,
                ),
            ],
            "Earlier period was higher.",
        )

        answer = response.json()["answer"]

        self.assertIn(
            "August 2025 spending: 200.00.",
            answer,
        )

        self.assertIn(
            "August 2026 spending: 100.00.",
            answer,
        )

    def test_equal_month_comparison(self):

        response, _ = self._post(
            "Compare July and August 2026 spending.",
            [
                row(
                    "2026-07-01",
                    "July",
                    debit=100.0,
                    balance=900.0,
                ),
                row(
                    "2026-08-01",
                    "August",
                    debit=100.0,
                    balance=800.0,
                ),
            ],
            "They were similar.",
        )

        self.assertIn(
            ("July 2026 and August 2026 " "had equal spending."),
            response.json()["answer"],
        )

    def test_second_month_higher(self):

        response, _ = self._post(
            "Compare July and August 2026 spending.",
            [
                row(
                    "2026-07-01",
                    "July",
                    debit=100.0,
                    balance=900.0,
                ),
                row(
                    "2026-08-01",
                    "August",
                    debit=200.0,
                    balance=700.0,
                ),
            ],
            "August was higher.",
        )

        self.assertIn(
            ("August 2026 spending was higher " "than July 2026 spending."),
            response.json()["answer"],
        )

    def test_multi_month_prompt_excludes_other_months(self):

        response, mock_llm = self._post(
            "Compare July and August 2026 spending.",
            [
                row(
                    "2026-07-01",
                    "July Purchase",
                    debit=100.0,
                    balance=900.0,
                ),
                row(
                    "2026-08-01",
                    "August Purchase",
                    debit=200.0,
                    balance=700.0,
                ),
                row(
                    "2026-09-01",
                    "September Purchase",
                    debit=300.0,
                    balance=400.0,
                ),
            ],
            "Comparison complete.",
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        prompt = mock_llm.call_args.args[0]

        self.assertIn(
            "July Purchase",
            prompt,
        )

        self.assertIn(
            "August Purchase",
            prompt,
        )

        self.assertNotIn(
            "September Purchase",
            prompt,
        )

    def test_multi_month_numeric_llm_is_discarded(self):

        response, _ = self._post(
            "Compare July and August 2026 spending.",
            [
                row(
                    "2026-07-01",
                    "July",
                    debit=100.0,
                    balance=900.0,
                ),
                row(
                    "2026-08-01",
                    "August",
                    debit=200.0,
                    balance=700.0,
                ),
            ],
            "July was 999 and August was 888.",
        )

        answer = response.json()["answer"]

        self.assertNotIn(
            "999",
            answer,
        )

        self.assertNotIn(
            "888",
            answer,
        )

    # =========================================================

    # EMPTY STATEMENT

    # =========================================================

    def test_empty_statement_exact_question(self):

        response, mock_llm = self._post(
            "How much did I spend?",
            [],
        )

        self.assertEqual(
            response.json()["answer"],
            ("No transactions are available " "in the uploaded statement."),
        )

        mock_llm.assert_not_called()

    def test_empty_statement_open_ended_question(self):

        response, mock_llm = self._post(
            "Summarize my statement.",
            [],
        )

        self.assertEqual(
            response.json()["answer"],
            ("No transactions are available " "in the uploaded statement."),
        )

        mock_llm.assert_not_called()

    def test_general_and_debit_transaction_counts_are_both_verified(self):

        response, mock_llm = self._post(
            (
                "How many transactions are there "
                "and how many debit transactions are there?"
            ),
            [
                row(
                    "2026-08-01",
                    "Debit A",
                    debit=10.0,
                    balance=990.0,
                ),
                row(
                    "2026-08-02",
                    "Credit",
                    credit=20.0,
                    balance=1010.0,
                ),
                row(
                    "2026-08-03",
                    "Debit B",
                    debit=30.0,
                    balance=980.0,
                ),
            ],
            "There are 999 transactions.",
        )

        answer = response.json()["answer"]

        self.assertIn(
            "Transaction count: 3.",
            answer,
        )

        self.assertIn(
            "Debit transaction count: 2.",
            answer,
        )

        self.assertNotIn(
            "999",
            answer,
        )

        mock_llm.assert_called_once()

    def test_general_and_credit_transaction_counts_are_both_verified(self):

        response, mock_llm = self._post(
            (
                "What is the transaction count "
                "and how many credit transactions are there?"
            ),
            [
                row(
                    "2026-08-01",
                    "Debit",
                    debit=10.0,
                    balance=990.0,
                ),
                row(
                    "2026-08-02",
                    "Credit A",
                    credit=20.0,
                    balance=1010.0,
                ),
                row(
                    "2026-08-03",
                    "Credit B",
                    credit=30.0,
                    balance=1040.0,
                ),
            ],
            "There are 888 transactions.",
        )

        answer = response.json()["answer"]

        self.assertIn(
            "Transaction count: 3.",
            answer,
        )

        self.assertIn(
            "Credit transaction count: 2.",
            answer,
        )

        self.assertNotIn(
            "888",
            answer,
        )

        mock_llm.assert_called_once()


if __name__ == "__main__":

    unittest.main()

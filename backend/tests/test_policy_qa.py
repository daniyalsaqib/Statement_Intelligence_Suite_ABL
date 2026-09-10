import unittest
from unittest.mock import patch

from fastapi import HTTPException

from backend.app.routers.policy_qa import (
    PolicyQuestion,
    ask_policy_question,
)


RELEVANT_RESULTS = [
    {
        "title": "Unclaimed Deposit Required Documents",
        "source": "https://www.abl.com/example-source",
        "content": "Required document information.",
        "distance": 0.20,
    },
    {
        "title": "Unclaimed Deposit Required Documents",
        "source": "https://www.abl.com/example-source",
        "content": "Additional required document information.",
        "distance": 0.30,
    },
]


class TestPolicyQA(unittest.TestCase):

    def test_relevant_policy_returns_answer_and_unique_sources(
        self,
    ):
        with patch(
            "backend.app.routers.policy_qa.search_policy_documents",
            return_value=RELEVANT_RESULTS,
        ), patch(
            "backend.app.routers.policy_qa.ask_llm",
            return_value="Required documents are listed in the policy.",
        ) as mock_llm:

            result = ask_policy_question(
                PolicyQuestion(
                    question=(
                        "What documents are required "
                        "for an unclaimed deposit?"
                    )
                )
            )

        self.assertEqual(
            result["answer"],
            "Required documents are listed in the policy.",
        )

        self.assertEqual(
            len(result["sources"]),
            1,
        )

        self.assertEqual(
            mock_llm.call_count,
            1,
        )

    def test_irrelevant_policy_fails_closed_without_llm(
        self,
    ):
        irrelevant_results = [
            {
                "title": "Unrelated",
                "source": "https://www.abl.com/unrelated",
                "content": "Unrelated information.",
                "distance": 0.90,
            }
        ]

        with patch(
            "backend.app.routers.policy_qa.search_policy_documents",
            return_value=irrelevant_results,
        ), patch(
            "backend.app.routers.policy_qa.ask_llm"
        ) as mock_llm:

            result = ask_policy_question(
                PolicyQuestion(
                    question="Something unrelated"
                )
            )

        self.assertEqual(
            result["sources"],
            [],
        )

        mock_llm.assert_not_called()

    def test_llm_failure_becomes_controlled_502(
        self,
    ):
        with patch(
            "backend.app.routers.policy_qa.search_policy_documents",
            return_value=RELEVANT_RESULTS,
        ), patch(
            "backend.app.routers.policy_qa.ask_llm",
            side_effect=RuntimeError(
                "provider failure"
            ),
        ):

            with self.assertRaises(
                HTTPException
            ) as context:

                ask_policy_question(
                    PolicyQuestion(
                        question=(
                            "What documents are required?"
                        )
                    )
                )

        self.assertEqual(
            context.exception.status_code,
            502,
        )

        self.assertNotIn(
            "provider failure",
            str(context.exception.detail),
        )


if __name__ == "__main__":
    unittest.main()

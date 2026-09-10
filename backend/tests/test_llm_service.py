import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.app.services import llm_service


class TestLLMService(unittest.TestCase):

    @patch.dict(
        os.environ,
        {"GROQ_API_KEY": ""},
        clear=False,
    )
    def test_missing_api_key_raises_error(self):
        with self.assertRaises(RuntimeError):
            llm_service.ask_llm("test")

    @patch.dict(
        os.environ,
        {
            "GROQ_API_KEY": "test-key",
            "GROQ_MODEL": "openai/gpt-oss-20b",
        },
        clear=False,
    )
    @patch(
        "backend.app.services.llm_service.Groq"
    )
    def test_successful_response(
        self,
        mock_groq,
    ):
        client = mock_groq.return_value

        client.chat.completions.create.return_value = (
            SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(
                            content="GROQ_OK"
                        )
                    )
                ]
            )
        )

        answer = llm_service.ask_llm(
            "Return GROQ_OK"
        )

        self.assertEqual(
            answer,
            "GROQ_OK",
        )

        kwargs = (
            client.chat.completions.create
            .call_args.kwargs
        )

        self.assertEqual(
            kwargs["model"],
            "openai/gpt-oss-20b",
        )

    @patch.dict(
        os.environ,
        {"GROQ_API_KEY": "test-key"},
        clear=False,
    )
    @patch(
        "backend.app.services.llm_service.Groq"
    )
    def test_empty_choices_returns_empty_string(
        self,
        mock_groq,
    ):
        client = mock_groq.return_value

        client.chat.completions.create.return_value = (
            SimpleNamespace(
                choices=[]
            )
        )

        answer = llm_service.ask_llm(
            "test"
        )

        self.assertEqual(
            answer,
            "",
        )


if __name__ == "__main__":
    unittest.main()

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import ai


class SessionHistoryTests(unittest.TestCase):
    def test_scan_history_is_owned_by_the_calling_session(self):
        first_session = []
        second_session = []

        ai.add_scan_to_history(first_session, "123", "Sample product", "Sample analysis")

        self.assertEqual(len(first_session), 1)
        self.assertEqual(first_session[0]["product_name"], "Sample product")
        self.assertEqual(second_session, [])

    def test_offline_analysis_updates_only_the_supplied_history_without_a_file(self):
        response = Mock(status_code=200)
        response.json.return_value = {"product": {"product_name": "Sample cereal"}}
        session_history = []

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(ai.requests, "get", return_value=response):
                with patch.dict(os.environ, {}, clear=True):
                    previous_dir = os.getcwd()
                    try:
                        os.chdir(temp_dir)
                        result = ai.ai_analysis("123", session_history)
                        self.assertIn("Demo (offline) analysis", result)
                        self.assertEqual(session_history[0]["product_name"], "Sample cereal")
                        self.assertFalse(Path("ai_analysis_history.json").exists())
                    finally:
                        os.chdir(previous_dir)

    def test_live_follow_up_uses_and_updates_only_the_supplied_session(self):
        first_session = [{
            "product_name": "Sample product",
            "ai_result": "Sample analysis",
            "chat_log": [],
        }]
        second_session = [{
            "product_name": "Other product",
            "ai_result": "Other analysis",
            "chat_log": [],
        }]
        response = Mock(status_code=200)
        response.json.return_value = {
            "choices": [{"message": {"content": "A sample response."}}]
        }

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-server-key"}, clear=True):
            with patch.object(ai.requests, "post", return_value=response) as post:
                result = ai.handle_follow_up("Is this suitable?", first_session)

        self.assertEqual(result, "A sample response.")
        self.assertEqual(first_session[0]["chat_log"], [{
            "user": "Is this suitable?",
            "ai": "A sample response.",
        }])
        self.assertEqual(second_session[0]["chat_log"], [])
        self.assertEqual(
            post.call_args.kwargs["headers"]["Authorization"],
            "Bearer test-server-key",
        )


if __name__ == "__main__":
    unittest.main()

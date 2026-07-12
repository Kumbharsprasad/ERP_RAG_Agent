import os
import unittest
from unittest.mock import patch, MagicMock
import json
import time

# Ensure we don't load real APIs
os.environ["GROQ_API_KEY"] = "mock_key"
os.environ["GEMINI_API_KEY"] = "mock_key"

from app.graph import app_graph, AgentState, parser_node, generate_section_node, assemble_docx_node
from app import parsers
from app import llm_gateway
from app.guardrails import validate_response_schema

class TestProductionFailureModes(unittest.TestCase):

    @patch("app.llm_gateway.litellm.completion")
    @patch("time.sleep")
    def test_rate_limit_pacing(self, mock_sleep, mock_completion):
        """
        Verify that consecutive completion calls trigger proactive rate limit delay and rolling token pacing.
        """
        # Mock successful litellm completion with usage info
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='{"content": "mock text"}'))]
        mock_response.usage = MagicMock(prompt_tokens=10, completion_tokens=10, total_tokens=20)
        mock_completion.return_value = mock_response

        # Configure environment variables for lower limits to force pacing easily
        os.environ["GROQ_MIN_DELAY_SECONDS"] = "2.0"
        os.environ["GROQ_TPM_LIMIT"] = "100"
        os.environ["GROQ_TPM_SAFE_RATIO"] = "0.80"  # Safe threshold = 80 tokens
        os.environ["GROQ_ESTIMATED_COMPLETION_TOKENS"] = "50"

        # Clear rolling window history
        llm_gateway.TOKEN_USAGE_HISTORY = []
        llm_gateway.LAST_CALL_TIME = 0.0

        # First call: history is empty, LAST_CALL_TIME is 0.0
        # No delay/pacing sleep should occur
        llm_gateway.generate_completion("Hello 1")
        self.assertEqual(mock_completion.call_count, 1)

        # Second call:
        # 1. Elapsed time since last call is very short (< 2.0s) -> should trigger minimum delay sleep.
        # 2. Total tokens: recent_tokens (20) + estimated_next (Hello 2 prompt length / 4 + estimated completion 50 = ~51) = 71.
        # 71 is under threshold (80), so no rolling limit sleep.
        llm_gateway.generate_completion("Hello 2")

        # Verify time.sleep was called for the minimum delay
        mock_sleep.assert_called()
        self.assertEqual(mock_completion.call_count, 2)

        # Force rolling limit sleep:
        # Add a large chunk to history to exceed threshold
        llm_gateway.TOKEN_USAGE_HISTORY.append((time.time(), 70))
        # Total recent tokens is now 20 + 70 = 90.
        # Threshold is 80.
        # Next call should sleep to wait for tokens to fall out of window.
        llm_gateway.generate_completion("Hello 3")
        self.assertEqual(mock_completion.call_count, 3)

    @patch("liteparse.LiteParse")
    def test_liteparse_fallback_warning(self, mock_liteparse_cls):
        """
        Verify that missing LibreOffice dependency triggers logfire warning
        and appends fallback warning to the LangGraph state.
        """
        # Mock LiteParse parser instance to raise dependency error
        mock_parser = MagicMock()
        mock_parser.parse.side_effect = Exception("LibreOffice is not installed or not working properly.")
        mock_liteparse_cls.return_value = mock_parser

        # We will parse a minimal DOCX bytes stream
        with patch("docx.Document") as mock_docx_doc:
            mock_doc_instance = MagicMock()
            mock_doc_instance.paragraphs = [MagicMock(text="Paragraph 1")]
            mock_docx_doc.return_value = mock_doc_instance

            # Call parse_file
            blocks, warnings = parsers.parse_file(b"dummy docx bytes", "document.docx")

            # Check that the fallback warnings were correctly populated
            self.assertTrue(len(warnings) > 0)
            self.assertIn("degraded fallback", warnings[0])
            self.assertIn("LibreOffice", warnings[0])

            # Verify graph node integrates this warning into state
            initial_state = {
                "user_request": "Draft SOP",
                "uploaded_files": [{"filename": "document.docx", "bytes": b"dummy docx bytes"}],
                "parsed_chunks": [],
                "warnings": []
            }
            final_state = parser_node(initial_state)
            self.assertTrue(len(final_state["warnings"]) > 0)
            self.assertIn("degraded fallback", final_state["warnings"][0])

    @patch("app.llm_gateway.generate_completion")
    def test_json_parse_failure_retry_and_partial_failure(self, mock_gen_completion):
        """
        Verify that malformed JSON response triggers completion retries,
        places fallback text, appends partial failure warning, sets partial_failure status,
        and results in valid schema compliance.
        """
        # Mock completion to return non-JSON text every time (always malformed)
        mock_gen_completion.return_value = "This is not JSON text at all!"

        initial_state = {
            "user_request": "Draft a document",
            "document_type": "SOP",
            "plan": ["Introduction"],
            "facts": {},
            "assumptions": [],
            "sections_content": {},
            "sources_used": [],
            "warnings": [],
            "status": ""
        }

        # Run generate_section_node
        final_state = generate_section_node(initial_state)

        # Check retries logic
        # Should call generate_completion exactly 4 times (max_attempts = 4)
        self.assertEqual(mock_gen_completion.call_count, 4)

        # Content should have the placeholder text
        self.assertIn("JSON parsing failed for section Introduction after 4 retries", final_state["sections_content"]["Introduction"])

        # Warnings should have the specific error
        self.assertTrue(any("JSON parsing failed after 4 retries for section: Introduction" in w for w in final_state["warnings"]))

        # Status should be set to partial_failure
        self.assertEqual(final_state["status"], "partial_failure")

        # Let's run assemble_docx_node on this state
        final_state_assembled = assemble_docx_node(final_state)

        # Status must still be partial_failure, not overwritten by success!
        self.assertEqual(final_state_assembled["status"], "partial_failure")
        self.assertTrue(os.path.exists(final_state_assembled["document_path"]))
        os.remove(final_state_assembled["document_path"])

        # Assert validate_response_schema succeeds for this partial failure response dictionary structure
        payload = {
            "status": final_state_assembled.get("status"),
            "document_type": final_state_assembled.get("document_type"),
            "plan": final_state_assembled.get("plan", []),
            "facts": final_state_assembled.get("facts", {}),
            "assumptions": final_state_assembled.get("assumptions", []),
            "data_source": "generated",
            "sources_used": final_state_assembled.get("sources_used", []),
            "warnings": final_state_assembled.get("warnings", []),
            "rejection_reason": None,
            "base64_document": "ZHVteWJhc2U2NA=="  # Dummy base64 string
        }
        self.assertTrue(validate_response_schema(payload))

if __name__ == "__main__":
    unittest.main()

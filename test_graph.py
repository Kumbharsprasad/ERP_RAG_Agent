import os
import unittest
import dotenv
from app.graph import app_graph

# Load environment variables
dotenv.load_dotenv()

def mock_generate_completion(user_prompt: str, system_prompt: str) -> str:
    user_prompt_lower = user_prompt.lower()
    system_prompt_lower = system_prompt.lower()
    
    # 1. intent guard mock
    if "intent guard" in system_prompt_lower:
        if "joke" in user_prompt_lower or "funny" in user_prompt_lower:
            return '{"is_business_query": false, "rejection_reason": "Request does not align with business document generation assistant intent. Request is for recreational content."}'
        else:
            return '{"is_business_query": true, "rejection_reason": ""}'
            
    # 2. classify doc mock
    if "classify" in system_prompt_lower or "classification" in system_prompt_lower:
        if "sop" in user_prompt_lower:
            return '{"document_type": "SOP"}'
        else:
            return '{"document_type": "Business Report"}'
            
    # 3. planner mock
    if "business analyst" in system_prompt_lower or "technical writer" in system_prompt_lower:
        if "sop" in user_prompt_lower:
            return '{"plan": ["Purpose and Scope", "Definition of Key Terms", "Leave Application Procedure"], "facts": {"PCCOE": "Pimpri Chinchwad College of Engineering"}, "assumptions": ["Mock assumption 1"]}'
        else:
            return '{"plan": ["Executive Summary", "Introduction to the People Strategy", "Key Themes and Goals"], "facts": {"PCCOE": "Pimpri Chinchwad College of Engineering"}, "assumptions": ["Mock assumption 2"]}'
        
    # 4. generate section mock
    if "writer" in system_prompt_lower or "generating content" in system_prompt_lower:
        return '{"content": "Mock generated section content body text.", "sources_used": []}'
        
    return '{"status": "unknown"}'

class TestStateGraph(unittest.TestCase):
    
    def setUp(self):
        from unittest.mock import patch
        self.patcher_completion = patch("app.llm_gateway.generate_completion", side_effect=mock_generate_completion)
        self.patcher_embedding = patch("app.llm_gateway.generate_embedding", return_value=[0.1]*1536)
        self.patcher_completion.start()
        self.patcher_embedding.start()

    def tearDown(self):
        self.patcher_completion.stop()
        self.patcher_embedding.stop()
    
    def test_graph_no_files(self):
        """
        Tests the compiled LangGraph with no uploaded files.
        Verifies that it defaults to generated source and produces a valid Word doc.
        """
        print("\n=== Running test_graph_no_files ===")
        input_state = {
            "user_request": "Draft a Standard Operating Procedure (SOP) for PCCOE leave application process",
            "session_id": "test_graph_session_no_files",
            "uploaded_files": [],
            "parsed_chunks": [],
            "retrieved_context": [],
            "document_type": "",
            "plan": [],
            "facts": {},
            "assumptions": [],
            "sections_content": {},
            "data_source": "",
            "sources_used": [],
            "status": "",
            "warnings": [],
            "document_path": ""
        }
        
        result = app_graph.invoke(input_state)
        
        print(f"Result Status: {result.get('status')}")
        print(f"Is Business Query: {result.get('is_business_query')}")
        print(f"Document Type: {result.get('document_type')}")
        print(f"Plan: {result.get('plan')}")
        print(f"Facts: {result.get('facts')}")
        print(f"Assumptions: {result.get('assumptions')}")
        print(f"Document Path: {result.get('document_path')}")
        print(f"Data Source: {result.get('data_source')}")
        
        self.assertEqual(result.get("status"), "success")
        self.assertTrue(result.get("is_business_query"))
        self.assertEqual(result.get("document_type"), "SOP")
        self.assertTrue(len(result.get("plan", [])) > 0)
        self.assertEqual(result.get("data_source"), "generated")
        
        doc_path = result.get("document_path", "")
        self.assertTrue(os.path.exists(doc_path))
        self.assertTrue(os.path.getsize(doc_path) > 0)
        
        # Clean up temp file
        if os.path.exists(doc_path):
            os.remove(doc_path)

    def test_graph_with_mock_files(self):
        """
        Tests the compiled LangGraph with an uploaded PowerPoint file.
        Verifies parser node, vector ingestion, retrieval, and referencing grounding.
        """
        print("\n=== Running test_graph_with_mock_files ===")
        pptx_path = "data/people_strategy_summary_slides.pptx"
        if not os.path.exists(pptx_path):
            self.skipTest("data/people_strategy_summary_slides.pptx not found for testing.")
            
        with open(pptx_path, "rb") as f:
            file_bytes = f.read()
            
        input_state = {
            "user_request": "Draft a business report summarizing the people strategy themes",
            "session_id": "test_graph_session_with_files",
            "uploaded_files": [{"filename": "people_strategy_summary_slides.pptx", "bytes": file_bytes}],
            "parsed_chunks": [],
            "retrieved_context": [],
            "document_type": "",
            "plan": [],
            "facts": {},
            "assumptions": [],
            "sections_content": {},
            "data_source": "",
            "sources_used": [],
            "status": "",
            "warnings": [],
            "document_path": ""
        }
        
        result = app_graph.invoke(input_state)
        
        print(f"Result Status: {result.get('status')}")
        print(f"Is Business Query: {result.get('is_business_query')}")
        print(f"Document Type: {result.get('document_type')}")
        print(f"Plan: {result.get('plan')}")
        print(f"Retrieved Context Count: {len(result.get('retrieved_context', []))}")
        print(f"Data Source: {result.get('data_source')}")
        print(f"Document Path: {result.get('document_path')}")
        
        self.assertEqual(result.get("status"), "success")
        self.assertTrue(result.get("is_business_query"))
        self.assertEqual(result.get("document_type"), "Business Report")
        self.assertTrue(len(result.get("retrieved_context", [])) > 0)
        self.assertEqual(result.get("data_source"), "user_upload")
        
        doc_path = result.get("document_path", "")
        self.assertTrue(os.path.exists(doc_path))
        self.assertTrue(os.path.getsize(doc_path) > 0)
        
        # Clean up temp file
        if os.path.exists(doc_path):
            os.remove(doc_path)

    def test_graph_rejection(self):
        """
        Tests the compiled LangGraph with an off-topic/non-business query.
        Verifies that intent guard correctly rejects it and terminates the flow.
        """
        print("\n=== Running test_graph_rejection ===")
        input_state = {
            "user_request": "Tell me a funny joke about software engineering and computers.",
            "session_id": "test_graph_session_rejection",
            "uploaded_files": [],
            "parsed_chunks": [],
            "retrieved_context": [],
            "document_type": "",
            "plan": [],
            "facts": {},
            "assumptions": [],
            "sections_content": {},
            "data_source": "",
            "sources_used": [],
            "status": "",
            "warnings": [],
            "document_path": ""
        }
        
        result = app_graph.invoke(input_state)
        
        print(f"Result Status: {result.get('status')}")
        print(f"Is Business Query: {result.get('is_business_query')}")
        print(f"Rejection Reason: {result.get('rejection_reason')}")
        
        self.assertEqual(result.get("status"), "rejected_non_business_query")
        self.assertFalse(result.get("is_business_query"))
        self.assertTrue(len(result.get("rejection_reason", "")) > 0)

if __name__ == "__main__":
    unittest.main()

import os
import unittest
import dotenv
from app.graph import app_graph

# Load environment variables
dotenv.load_dotenv()

class TestStateGraph(unittest.TestCase):
    
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

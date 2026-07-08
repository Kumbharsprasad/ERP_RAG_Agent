import os
import time
import random
import unittest
import app.vector_store
import app.llm_gateway

# Automatically detect if API keys are configured.
# If not, monkey-patch the embedding generator to run tests in mock mode.
USE_MOCK = not os.getenv("GEMINI_API_KEY")

if USE_MOCK:
    print("=" * 70)
    print("WARNING: GEMINI_API_KEY not set. Running tests in MOCK EMBEDDING MODE.")
    print("Vector similarity scores in this run will be random.")
    print("=" * 70)
    
    def mock_generate_embedding(text: str) -> list[float]:
        # Generate a deterministic pseudo-random embedding vector of size 768
        random.seed(abs(hash(text)))
        return [random.uniform(-1, 1) for _ in range(768)]
        
    app.vector_store.generate_embedding = mock_generate_embedding
    app.llm_gateway.generate_embedding = mock_generate_embedding
else:
    print("=" * 70)
    print("GEMINI_API_KEY detected. Running tests with REAL Gemini embeddings.")
    print("=" * 70)


class TestVectorPipeline(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        cls.collection_name = "test_enterprise_collection"
        
        # Dynamically determine vector size from the embedding generator
        try:
            sample_emb = app.vector_store.generate_embedding("test")
            cls.vector_size = len(sample_emb)
        except Exception:
            cls.vector_size = 768
            
        # Delete the collection if it exists to reset dimension settings
        try:
            app.vector_store.client.delete_collection(cls.collection_name)
        except Exception:
            pass
            
        # Verify collection creation
        print(f"Creating collection '{cls.collection_name}' with vector size {cls.vector_size} if not exists...")
        app.vector_store.create_collection_if_not_exists(
            collection_name=cls.collection_name, 
            vector_size=cls.vector_size
        )
        
    def test_pipeline(self):
        # 1. Prepare sample chunks for two different sessions
        session_a = "session_alice_123"
        session_b = "session_bob_999"
        
        chunks_a = [
            {"text": "Python is a popular programming language.", "source_file": "doc1.txt", "location": "Block 1", "chunk_index": 0},
            {"text": "FastAPI is a modern, fast (high-performance) web framework.", "source_file": "doc1.txt", "location": "Block 2", "chunk_index": 1},
        ]
        
        chunks_b = [
            {"text": "Cooking pasta requires boiling water and adding salt.", "source_file": "recipe.txt", "location": "Block 1", "chunk_index": 0},
            {"text": "Baking cookies requires flour, sugar, and chocolate chips.", "source_file": "recipe.txt", "location": "Block 2", "chunk_index": 1},
        ]
        
        # 2. Upsert chunks for Session A
        print(f"Upserting chunks for {session_a}...")
        app.vector_store.upsert_chunks(chunks_a, session_id=session_a, collection_name=self.collection_name)
        
        # 3. Upsert chunks for Session B
        print(f"Upserting chunks for {session_b}...")
        app.vector_store.upsert_chunks(chunks_b, session_id=session_b, collection_name=self.collection_name)
        
        # 4. Search within Session A
        query = "Tell me about programming or FastAPI"
        print(f"Searching for query '{query}' in {session_a}...")
        results_a = app.vector_store.retrieve_relevant_chunks(
            query=query, 
            session_id=session_a, 
            top_k=5, 
            collection_name=self.collection_name
        )
        
        print(f"Retrieved {len(results_a)} results for {session_a}:")
        for idx, res in enumerate(results_a):
            print(f"  Result {idx}: score={res['score']:.4f}, file={res['source_file']}, text='{res['text']}'")
            
        # Verify Session A results belong only to doc1.txt (Session A's file)
        # and that no cross-session leakage from Session B occurred.
        for res in results_a:
            self.assertEqual(res["source_file"], "doc1.txt", f"Data leakage detected! Found {res['source_file']} in search of {session_a}")
            
        # 5. Search within Session B
        query_b = "Tell me about food and cooking"
        print(f"\nSearching for query '{query_b}' in {session_b}...")
        results_b = app.vector_store.retrieve_relevant_chunks(
            query=query_b, 
            session_id=session_b, 
            top_k=5, 
            collection_name=self.collection_name
        )
        
        print(f"Retrieved {len(results_b)} results for {session_b}:")
        for idx, res in enumerate(results_b):
            print(f"  Result {idx}: score={res['score']:.4f}, file={res['source_file']}, text='{res['text']}'")
            
        for res in results_b:
            self.assertEqual(res["source_file"], "recipe.txt", f"Data leakage detected! Found {res['source_file']} in search of {session_b}")
            
        # 6. Test cleanup function
        # Points upserted just now have created_at = current time.
        # Run cleanup with max_age_seconds = -1 to delete everything.
        print("\nTesting cleanup_old_sessions...")
        deleted_count = app.vector_store.cleanup_old_sessions(
            max_age_seconds=-1, 
            collection_name=self.collection_name
        )
        print(f"Deleted {deleted_count} old points.")
        self.assertGreaterEqual(deleted_count, 4, "Cleanup did not delete the test points.")
        
        # Verify that they are indeed gone
        post_cleanup_results = app.vector_store.retrieve_relevant_chunks(
            query="Python", 
            session_id=session_a, 
            top_k=5, 
            collection_name=self.collection_name
        )
        self.assertEqual(len(post_cleanup_results), 0, "Points were not fully deleted during cleanup.")
        print("[PASS] Cleanup successfully removed expired session data.")

def main():
    suite = unittest.TestLoader().loadTestsFromTestCase(TestVectorPipeline)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

if __name__ == "__main__":
    main()

import os
import time
import dotenv
from app.parsers import parse_file
from app.chunking import chunk_text
from app.vector_store import create_collection_if_not_exists, upsert_chunks, client

def main():
    # Load environment variables from .env
    dotenv.load_dotenv()
    
    # 1. Define configuration
    collection_name = "enterprise_rag_chunks"
    session_id = "default_enterprise_session"
    data_dir = "data"
    files_to_ingest = ["hrpolicy.pdf", "people_strategy_summary_slides.pptx"]
    
    # Check if QDRANT_URL and GEMINI_API_KEY are configured
    qdrant_url = os.getenv("QDRANT_URL")
    gemini_key = os.getenv("GEMINI_API_KEY")
    if not qdrant_url or not gemini_key:
        print("[ERROR] QDRANT_URL or GEMINI_API_KEY environment variables are missing in your .env file!")
        print("Please check your .env file and set valid credentials before running ingestion.")
        return
        
    print(f"Connecting to Qdrant Cloud at {qdrant_url}...")
    print(f"Ensuring Qdrant collection '{collection_name}' exists (configured for 3072 dimensions)...")
    
    # 2. Create the collection in Qdrant with 3072 dimensions (output dimension of gemini-embedding-001)
    create_collection_if_not_exists(collection_name=collection_name, vector_size=3072)
    
    # 3. Process each file
    for filename in files_to_ingest:
        file_path = os.path.join(data_dir, filename)
        if not os.path.exists(file_path):
            print(f"[WARNING] File not found: {file_path}. Skipping.")
            continue
            
        print(f"\nProcessing '{file_path}'...")
        start_time = time.time()
        
        # Read file bytes in memory
        with open(file_path, "rb") as f:
            file_bytes = f.read()
            
        print(f"  Read {len(file_bytes)} bytes. Parsing content...")
        try:
            # Parse
            parsed_blocks = parse_file(file_bytes, filename)
            print(f"  Extracted {len(parsed_blocks)} block(s) from document.")
            
            # Chunk
            print("  Chunking extracted content...")
            chunks = chunk_text(parsed_blocks, chunk_size_tokens=400, overlap_ratio=0.15)
            print(f"  Generated {len(chunks)} chunk(s).")
            
            # Upsert into Qdrant
            print(f"  Generating embeddings and uploading to Qdrant under session '{session_id}'...")
            upsert_chunks(chunks, session_id=session_id, collection_name=collection_name)
            
            duration = time.time() - start_time
            print(f"[SUCCESS] Successfully ingested '{filename}' in {duration:.2f} seconds!")
            
        except Exception as e:
            print(f"[ERROR] Failed to ingest '{filename}': {e}")
            import traceback
            traceback.print_exc()
            
    print("\nIngestion process complete!")

if __name__ == "__main__":
    main()

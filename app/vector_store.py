import os
import uuid
import time
from qdrant_client import QdrantClient
from qdrant_client.http import models
import logfire
from app.llm_gateway import generate_embedding

# Retrieve Qdrant credentials from environment
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

# Initialize client. Fall back to :memory: if QDRANT_URL is not set for local testing/verification.
if QDRANT_URL:
    client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=60.0)
else:
    # Use in-memory fallback for local verification/testing if no env vars are defined
    client = QdrantClient(":memory:")

def create_collection_if_not_exists(collection_name="enterprise_rag_chunks", vector_size=768) -> None:
    """
    Creates the collection in Qdrant with Cosine distance if it doesn't already exist.
    Note: Gemini's text-embedding-004 output dimension defaults to 768. Confirm if using other models.
    """
    collections_res = client.get_collections()
    exists = any(c.name == collection_name for c in collections_res.collections)
    if not exists:
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE
            )
        )
        
    # Attempt index creation to ensure they exist on both new and pre-existing collections
    try:
        client.create_payload_index(
            collection_name=collection_name,
            field_name="session_id",
            field_schema=models.PayloadSchemaType.KEYWORD
        )
    except Exception:
        pass
        
    try:
        client.create_payload_index(
            collection_name=collection_name,
            field_name="created_at",
            field_schema=models.PayloadSchemaType.INTEGER
        )
    except Exception:
        pass

def upsert_chunks(chunks: list[dict], session_id: str, collection_name="enterprise_rag_chunks") -> None:
    """
    Upserts a list of document chunks into Qdrant.
    Generates embedding for each chunk via the LLM gateway.
    Runs automated session cleanup first to prevent unbounded database growth.
    """
    with logfire.span("Upserting {num_chunks} chunks for session {session_id}", num_chunks=len(chunks), session_id=session_id):
        # Clean up old sessions first before doing new upserts
        cleanup_old_sessions(collection_name=collection_name)
        
        points = []
        current_time = int(time.time())
        
        for chunk in chunks:
            text = chunk.get("text", "")
            # Generate embedding
            embedding = generate_embedding(text)
            
            point_id = str(uuid.uuid4())
            payload = {
                "session_id": session_id,
                "source_file": chunk.get("source_file", ""),
                "location": chunk.get("location", ""),
                "text": text,
                "chunk_index": chunk.get("chunk_index", 0),
                "created_at": current_time
            }
            
            points.append(
                models.PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload=payload
                )
            )
            
        if points:
            # Upsert in batches of 20 to avoid write timeouts on remote clients
            batch_size = 20
            num_batches = (len(points) + batch_size - 1) // batch_size
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                batch_num = i // batch_size + 1
                logfire.info("Uploading batch {batch_num}/{total_batches} ({batch_len} points)", batch_num=batch_num, total_batches=num_batches, batch_len=len(batch))
                client.upsert(
                    collection_name=collection_name,
                    points=batch
                )
            logfire.info("Successfully upserted all {num_chunks} chunks.", num_chunks=len(chunks))

def retrieve_relevant_chunks(
    query: str, 
    session_id: str, 
    top_k=5, 
    collection_name="enterprise_rag_chunks"
) -> list[dict]:
    """
    Generates embedding for the query and searches Qdrant for similar vectors,
    filtered to matches belonging only to the specified session_id.
    """
    with logfire.span("Retrieving relevant chunks for query: '{query}'", query=query, session_id=session_id):
        query_vector = generate_embedding(query)
        
        response = client.query_points(
            collection_name=collection_name,
            query=query_vector,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="session_id",
                        match=models.MatchValue(value=session_id)
                    )
                ]
            ),
            limit=top_k
        )
        
        results = []
        for hit in response.points:
            payload = hit.payload or {}
            results.append({
                "score": hit.score,
                "source_file": payload.get("source_file", ""),
                "location": payload.get("location", ""),
                "text": payload.get("text", "")
            })
        logfire.info("Retrieved {num_results} matched points.", num_results=len(results))
        return results

def cleanup_old_sessions(max_age_seconds=3600, collection_name="enterprise_rag_chunks") -> int:
    """
    Deletes all vectors from the specified collection where the payload's 'created_at'
    timestamp is older than max_age_seconds from now.
    Returns the count of deleted points.
    """
    cutoff_time = int(time.time()) - max_age_seconds
    filter_cond = models.Filter(
        must=[
            models.FieldCondition(
                key="created_at",
                range=models.Range(lt=cutoff_time)
            )
        ]
    )
    
    with logfire.span("Checking and cleaning up expired sessions"):
        try:
            # Count how many points match the filter before deletion
            count_res = client.count(
                collection_name=collection_name,
                count_filter=filter_cond
            )
            num_to_delete = count_res.count
            
            if num_to_delete > 0:
                client.delete(
                    collection_name=collection_name,
                    points_selector=models.FilterSelector(filter=filter_cond)
                )
                logfire.info("Deleted {num_to_delete} expired session vectors.", num_to_delete=num_to_delete)
            else:
                logfire.info("No expired session vectors found.")
            return num_to_delete
        except Exception as e:
            logfire.warn("Session cleanup skipped or failed: {error}", error=str(e))
            # Handle cases where collection does not exist yet gracefully
            return 0

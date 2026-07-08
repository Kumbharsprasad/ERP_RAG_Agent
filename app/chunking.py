import tiktoken
import logfire

def chunk_text(parsed_blocks: list[dict], chunk_size_tokens=400, overlap_ratio=0.15) -> list[dict]:
    """
    Chunks parsed blocks of text.
    For non-CSV blocks: uses a token-based sliding window.
    For CSV blocks: splits at row boundaries only, keeping column headers at the start of each chunk.
    Preserves original 'source_file' and 'location' metadata, adding a unique 'chunk_index' for each.
    """
    with logfire.span("Chunking {num_blocks} blocks", num_blocks=len(parsed_blocks)):
        chunks = _chunk_text_impl(parsed_blocks, chunk_size_tokens, overlap_ratio)
        logfire.info("Chunking complete. Generated {num_chunks} chunks.", num_chunks=len(chunks))
        return chunks

def _chunk_text_impl(parsed_blocks: list[dict], chunk_size_tokens=400, overlap_ratio=0.15) -> list[dict]:
    encoding = tiktoken.get_encoding("cl100k_base")
    overlap_tokens = int(chunk_size_tokens * overlap_ratio)
    
    # Safety checks
    if overlap_tokens >= chunk_size_tokens:
        overlap_tokens = max(0, chunk_size_tokens - 1)
        
    chunks = []
    
    for block in parsed_blocks:
        text = block.get("text", "").strip()
        if not text:
            continue
        source_file = block.get("source_file", "")
        location = block.get("location", "")
        
        # Check if the block is from CSV
        is_csv = source_file.lower().endswith(".csv") or (location and location.startswith("Rows"))
        
        if is_csv:
            lines = text.splitlines()
            if not lines:
                continue
            
            header = lines[0]
            data_rows = lines[1:]
            
            # If the entire CSV block fits within token limits, keep it as is
            tokens_count = len(encoding.encode(text))
            if tokens_count <= chunk_size_tokens:
                chunks.append({
                    "text": text,
                    "source_file": source_file,
                    "location": location,
                    "chunk_index": 0
                })
                continue
                
            # Otherwise, split at row boundaries
            start = 0
            chunk_idx = 0
            while start < len(data_rows):
                end = start
                current_rows = []
                while end < len(data_rows):
                    candidate_rows = current_rows + [data_rows[end]]
                    candidate_text = header + "\n" + "\n".join(candidate_rows)
                    candidate_tokens = len(encoding.encode(candidate_text))
                    
                    if candidate_tokens <= chunk_size_tokens or len(current_rows) == 0:
                        current_rows.append(data_rows[end])
                        end += 1
                    else:
                        break
                
                chunk_text_str = header + "\n" + "\n".join(current_rows)
                chunks.append({
                    "text": chunk_text_str,
                    "source_file": source_file,
                    "location": location,
                    "chunk_index": chunk_idx
                })
                chunk_idx += 1
                
                if end == len(data_rows):
                    break
                    
                # Determine overlap
                # Walk backward to find overlapping rows
                next_start = end - 1
                while next_start > start:
                    overlap_rows = data_rows[next_start:end]
                    overlap_candidate = header + "\n" + "\n".join(overlap_rows)
                    overlap_tokens_count = len(encoding.encode(overlap_candidate))
                    if overlap_tokens_count <= overlap_tokens:
                        next_start -= 1
                    else:
                        break
                
                next_start = max(next_start + 1, start + 1)
                start = next_start
                
        else:
            # Standard token-based sliding window
            tokens = encoding.encode(text)
            num_tokens = len(tokens)
            
            if num_tokens <= chunk_size_tokens:
                chunks.append({
                    "text": text,
                    "source_file": source_file,
                    "location": location,
                    "chunk_index": 0
                })
                continue
                
            step_size = chunk_size_tokens - overlap_tokens
            if step_size <= 0:
                step_size = 1
                
            chunk_idx = 0
            start = 0
            while start < num_tokens:
                end = min(start + chunk_size_tokens, num_tokens)
                chunk_tokens = tokens[start:end]
                chunk_text_str = encoding.decode(chunk_tokens)
                
                chunks.append({
                    "text": chunk_text_str,
                    "source_file": source_file,
                    "location": location,
                    "chunk_index": chunk_idx
                })
                chunk_idx += 1
                
                if end == num_tokens:
                    break
                    
                start += step_size
                
    return chunks

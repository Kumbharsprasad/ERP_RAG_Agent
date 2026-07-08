# ERP Agent - Phase 1: In-Memory File Parsing and Chunking

This module is Phase 1 of a larger RAG (Retrieval-Augmented Generation) pipeline. It provides capabilities to ingest, parse, and chunk documents of various formats completely in-memory, without writing uploaded files to disk.

## Supported File Types

- **PDF (`.pdf`)**: Parsed using `pdfplumber` page-by-page.
- **DOCX (`.docx`)**: Parsed using `python-docx` grouped into blocks of 10 paragraphs.
- **PPTX (`.pptx`)**: Parsed using `python-pptx` slide-by-slide.
- **HTML (`.html`, `.htm`)**: Parsed using `BeautifulSoup` splitting into sections based on heading tags (`<h1>`-`<h6>`).
- **CSV (`.csv`)**: Parsed using `pandas` into blocks of 20 rows, preserving column headers in each block.
- **TXT (`.txt`)**: Decoded directly and split into ~500-word blocks.

## Key Features

- **In-Memory Operations**: All files are parsed directly from byte streams using `io.BytesIO`. No disk I/O is performed.
- **Metadata Preservation**: Every extracted chunk retains its originating file name (`source_file`), exact document coordinates (`location`, e.g., page number, paragraph indices, row ranges, slide number), and a relative `chunk_index`.
- **Token-Aware Chunking**: Uses `tiktoken` with the `cl100k_base` encoding (compatible with OpenAI models like `gpt-4` and `text-embedding-3-small`) to respect max token limits.
- **Row-Boundary Awareness**: When chunking CSV files, row-level integrity is maintained. Individual rows are never split across chunks, and column headers are dynamically attached to the start of every sub-chunk.

## Phase 2: Embedding & Vector Store Integration

Phase 2 adds the core retrieval and generation gateway.

### LLM Gateway (`app/llm_gateway.py`)

- **Embedding Generation**: Calls Gemini's `text-embedding-004` (768 dimensions) via LiteLLM.
- **Completion Generation**: Calls Groq's `llama-3.1-8b-instant` via LiteLLM.
- **Robust Retry Logic**: Both wrappers incorporate a retry decorator enforcing up to 3 retries (4 attempts total) with exponential backoff (`1s`, `2s`, `4s`) on failure. All failures that exhaust these retries raise a custom `LLMGatewayError`.

### Vector Store (`app/vector_store.py`)

- **Qdrant Cloud Client**: Connects to Qdrant Cloud using `QDRANT_URL` and `QDRANT_API_KEY` (falls back to a local `:memory:` instance for offline testing).
- **Session-Based Isolation**: Points are upserted with metadata containing `session_id`, `source_file`, `location`, `text`, `chunk_index`, and `created_at`. All retrievals are strictly filtered to the current `session_id` using Qdrant's `FieldCondition`. This guarantees that no session's uploaded data is ever leaked to or retrievable by another session.
- **Unbounded Growth Mitigation**: At the start of a session's first upsert, an automated cleanup task (`cleanup_old_sessions`) is triggered, which deletes all vectors older than a configurable expiration window (defaults to 3600 seconds) from Qdrant.

## Logfire Observability

Pydantic Logfire is integrated for structured logging and trace observability. It tracks document parsing, text chunking, LLM gateway API requests, retries, vector database upserts, and search retrievals.

### Target Project Details
- **Logfire Organization**: `prasadnkumbhar`
- **Logfire Project**: `starter-project` (configured in `app/__init__.py`)
- **Logfire Base URL**: `https://logfire-us.pydantic.dev`

### Authentication & Setup

#### Local CLI Authentication (OAuth)
To authenticate your local development environment to send traces to the custom US-hosted instance of Logfire, run the following commands:
```powershell
# Authenticate CLI with custom US base URL
.\agentvenv\Scripts\logfire --base-url="https://logfire-us.pydantic.dev" auth

# Select the organization and project
.\agentvenv\Scripts\logfire --base-url="https://logfire-us.pydantic.dev" projects use --org "prasadnkumbhar" "starter-project"
```

#### Production / Container Authentication
For containerized or deployed environments, set the following environment variable:
- `LOGFIRE_TOKEN`: Set this to your Logfire write token. If set, the SDK automatically authenticates and streams traces to the cloud platform without CLI configuration.

*Note: If no token or CLI credentials are set, the SDK gracefully falls back to local-only console logging without interrupting application imports or test suites.*

## Phase 3: LangGraph Agent Orchestration

Phase 3 implements the core agent loop using `langgraph` to coordinate document classification, context retrieval, structure planning, dynamic content generation, and file assembly.

### StateGraph Flow Diagram

```
       Entry
         │
         ▼
  [intent_guard] ──(is_business_query=False)──► [rejection_node] ──► END
         │
         ▼ (is_business_query=True)
   [file_check] ──(has_files=False)──┐
         │                           │
         ▼ (has_files=True)          │
     [parser]                        │
         │                           │
         ▼                           │
  [chunk_and_embed]                  │
         │                           │
         ▼                           ▼
  [retrieve_context] ◄───────────────┘
         │
         ▼
  [classify_document_type]
         │
         ▼
       [plan] ◄────────────────────────────────────┐
         │                                         │
         ├───(len(sections_content) < len(plan))──► [generate_section]
         │
         ▼ (len(sections_content) == len(plan))
   [assemble_docx] ──► END
```

### Graph Nodes Description

1. **`intent_guard`**: Classifies if the query is a valid business document request. Casual chats or instruction override attempts are sent to `rejection_node`.
2. **`file_check`**: Directs the execution flow depending on whether files were uploaded.
3. **`parser`**: Reads uploaded documents from bytes in memory and parses them into raw text blocks.
4. **`chunk_and_embed`**: Splits blocks into token-size sliding windows and indexes them in Qdrant with session separation.
5. **`retrieve_context`**: Queries Qdrant for matching context (if files were uploaded) and sets the `data_source` variable.
6. **`classify_document_type`**: Maps the query to a specific category (Proposal, SOP, Project Plan, etc.) to set Tone Guidance.
7. **`plan`**: Generates a section layout, key details facts list, and explicit assumptions list.
8. **`generate_section`**: Focuses on generating a single section of the document. Loops back to itself dynamically until all planned sections are populated.
9. **`assemble_docx`**: Assembles headings, content, assumptions, and referenced sources into a `.docx` file using `python-docx`.

## Phase 4: API Layer, Guardrails, and Observability

Phase 4 introduces a FastAPI web application layer to serve the document generation pipeline. It includes safety guardrails (length limits, injection guards, PII leakage detection, schema compliance) and deep Logfire observability.

### API Endpoints

1. **`GET /health`**
   - Liveness probe confirming API operational health.
   - Verifies network connectivity and collection query access directly to the Qdrant database.

2. **`POST /agent`**
   - Receives form parameter `request` (prompt text) and optional list of multipart `files` (allowed extensions: PDF, DOCX, PPTX, HTML, CSV, TXT; max 5 files, 10MB each).
   - Validates the prompt using safety guardrails.
   - Routes files directly through memory to compile doc embeddings in Qdrant (with session isolation).
   - Runs the multi-node LangGraph generator.
   - Evaluates the output text sections for newly introduced PII leaks.
   - Serializes metadata and encodes the finished Word doc as a base64 string in a structured JSON payload matching our Pydantic response schema.

### Integrated Safety Guardrails

- **Input Prompt Validation**: Limits prompt inputs to a maximum of 2000 characters and runs case-insensitive regex checks for prompt injection keywords (e.g. `ignore previous instructions`, `reveal system prompt`).
- **PII Leakage Scanning**: Scans generated text sections for emails, phone numbers, and SSNs. If PII is found that was *not* present in the original uploaded/retrieved context, a warning is raised in the response metadata.
- **Pydantic Response Schema Compliance**: Validates the final API response against the `AgentAPIResponse` Pydantic model before returning, ensuring schema conformance.

### Logfire Pipeline Observability

The application leverages OpenTelemetry integration through Pydantic Logfire:
- **FastAPI Instrumentation**: `logfire.instrument_fastapi(app)` automatically tracks incoming HTTP requests, response status codes, route durations, and payloads.
- **LangGraph Node Spans**: The execution of the agent state graph is wrapped in `logfire.span(...)` segments. This provides developers with instant visibility into individual node processing times, inputs, outputs, and any internal exception tracebacks without modifying print statement logs.

## Phase 5: Streamlit Frontend & Multi-Service Deployment

Phase 5 introduces a Streamlit user interface as the primary client, alongside deployment configurations for production environments.

### Core Architecture Flow

```
┌─────────────────┐
│  Streamlit App  │ (User-facing frontend)
└────────┬────────┘
         │ (HTTP Form + Multi-File upload)
         ▼
┌─────────────────┐
│   FastAPI App   │ (Main API Service - app.main)
└────────┬────────┘
         │ (Invokes graph wrapped in Logfire spans)
         ▼
┌─────────────────┐
│ LangGraph Agent │ (Dynamic State Machine - app.graph)
└────┬───┬───┬────┘
     │   │   │   └──────────────────────┐
     │   │   └───────────────┐          │
     ▼   ▼                   ▼          ▼
┌──────────────┐     ┌───────────┐ ┌─────────┐
│  Qdrant DB   │     │ Gemini/   │ │ Logfire │ (Traces and metrics)
│ (Vector RAG) │     │ Groq LLM  │ └─────────┘
└──────────────┘     └───────────┘
```

### Running the Project Locally

#### 1. Setup Environment Variables
Create a `.env` file in the root directory:
```properties
# LLM Providers API Keys
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here

# Qdrant Vector Store Configuration
QDRANT_URL=your_qdrant_cluster_endpoint_url
QDRANT_API_KEY=your_qdrant_cluster_api_key

# Logfire Write Token (Optional for cloud traces, falls back to console if unset)
LOGFIRE_TOKEN=your_logfire_token_here

# Frontend Configuration
BACKEND_API_URL=http://localhost:8000
```

#### 2. Start the Backend API
Run the FastAPI backend on port 8000:
```powershell
.\agentvenv\Scripts\python -m uvicorn app.main:app --port 8000 --reload
```

#### 3. Start the Streamlit Frontend
Run the Streamlit app in a separate terminal:
```powershell
.\agentvenv\Scripts\streamlit run streamlit_app.py
```

### Deployment Configuration

#### FastAPI Backend (Render)
The repository contains a declarative `render.yaml` configuration. To deploy:
1. Connect this repository to your **Render** dashboard.
2. Render will automatically parse the `render.yaml` template, creating a web service running `uvicorn app.main:app` on port 10000.
3. Configure the environment variables (`GROQ_API_KEY`, `GEMINI_API_KEY`, `QDRANT_URL`, `QDRANT_API_KEY`, `LOGFIRE_TOKEN`) directly in Render's Env Settings dashboard.

#### Streamlit UI (Streamlit Community Cloud)
The Streamlit application can be deployed for free on **Streamlit Community Cloud**:
1. Connect the git repository to Streamlit Community Cloud.
2. Specify the entry point file as `streamlit_app.py`.
3. Under the app's advanced settings, define the production FastAPI backend endpoint:
   ```toml
   BACKEND_API_URL = "https://your-deployed-fastapi-backend-url.onrender.com"
   ```

---

## Project Phase Summaries

1. **Phase 1: Ingestion & Parsing**
   - Implemented standard and scanned PDF text extraction with `pdfplumber` and `pytesseract` OCR fallbacks.
   - Built slideshow slides text parser (`python-pptx`) and spreadsheet tab parser (`pandas`).
2. **Phase 2: RAG Vector Pipeline**
   - Wired up Gemini embedding generator and indexed content in Qdrant with token sliding windows and session-id TTL cleanup.
   - Implemented GROQ llama-3.1-8b completions with backoff retry logic.
3. **Phase 3: LangGraph Agent Loop**
   - Created the `AgentState` mapping and assembled the LangGraph node routing network.
   - Designed off-topic intent rejections, classification routing, document layout planning, dynamic loop section generation, and final `.docx` assembly.
4. **Phase 4: API Layer & Safety Guards**
   - Built FastAPI routes (`/agent` and `/health`) with Logfire server-side request tracing.
   - Implemented length limits, injection detectors, post-generation PII leakage scanners, and Pydantic response schema checks.
5. **Phase 5: User Interface & Deployment**
   - Designed a clean sidebar-powered Streamlit client with preset document requests, multipart RAG uploads, visual step-progress trackers, and document file download triggers.
   - Provided declarative Render configurations (`render.yaml`) and multi-environment variables orchestration.

## Future Phases

- **Phase 6**: Agentic search execution (LangGraph agent, memory, guardrails, RAG completion).

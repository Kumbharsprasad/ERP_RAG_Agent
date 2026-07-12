import os
import uuid
import base64
import logfire
from fastapi import FastAPI, Form, File, UploadFile, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional

from app.graph import app_graph
from app.vector_store import client as qdrant_client
from app import guardrails

# Initialize FastAPI
app = FastAPI(title="ERP RAG Agent API")

# Add CORS Middleware to allow requests from local dev and production vercel domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instrument FastAPI with logfire
logfire.instrument_fastapi(app)

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".pptx", ".xlsx", ".html", ".htm", ".csv", ".txt", ".png", ".jpg", ".jpeg"}
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB

import shutil

@app.get("/health")
def health_check():
    """
    Liveness check that confirms API state, Qdrant client connection, and LibreOffice availability.
    """
    try:
        # Check Qdrant collection status
        qdrant_client.get_collections()
        qdrant_status = "healthy"
    except Exception as e:
        qdrant_status = f"unhealthy ({str(e)})"
        logfire.warn("Health check: Qdrant client is unhealthy. Error: {error}", error=str(e))
        
    # Check LibreOffice availability on host
    libreoffice_available = bool(shutil.which("libreoffice") or shutil.which("soffice"))
    
    return {
        "status": "healthy",
        "qdrant": qdrant_status,
        "libreoffice": "available" if libreoffice_available else "not_available"
    }

@app.post("/agent")
async def execute_agent(
    request: Optional[str] = Form(None, description="The user document generation prompt"),
    files: Optional[List[UploadFile]] = File(None, description="Optional uploaded context files (Max 5, 10MB each)")
):
    """
    Triggers the LangGraph agent to generate the requested enterprise document.
    Runs input and output guardrails, and returns base64-encoded Word document bytes.
    """
    # 1. Validate Input request text
    if request is None:
        request = ""
    is_valid_input, input_err = guardrails.validate_input(request)
    if not is_valid_input:
        logfire.warn("Input validation failed: {error}", error=input_err)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=input_err
        )
        
    # 2. Validate Uploaded Files
    uploaded_files = []
    if files:
        if len(files) > 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum of 5 files can be uploaded."
            )
            
        for f in files:
            # Check file extension
            _, ext = os.path.splitext(f.filename)
            if ext.lower() not in ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported file type: '{f.filename}'. Allowed: PDF, DOCX, PPTX, XLSX, HTML, CSV, TXT, PNG, JPG, JPEG"
                )
                
            # Check file size (by reading and checking bytes count)
            file_bytes = await f.read()
            if len(file_bytes) > MAX_FILE_SIZE_BYTES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"File '{f.filename}' exceeds the 10MB size limit."
                )
                
            uploaded_files.append({
                "filename": f.filename,
                "bytes": file_bytes
            })
            
    # 3. Generate Session ID and Initial AgentState
    session_id = str(uuid.uuid4())
    initial_state = {
        "user_request": request,
        "session_id": session_id,
        "uploaded_files": uploaded_files,
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
    
    # 4. Invoke the LangGraph flow
    try:
        with logfire.span("Executing LangGraph Agent Flow"):
            result = app_graph.invoke(initial_state)
    except Exception as e:
        logfire.exception("Unhandled error during graph execution: {error}", error=str(e))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": "An internal error occurred while generating the document."
            }
        )
        
    # 5. Output Validation (PII scanning)
    sections_content = result.get("sections_content") or {}
    retrieved_context = result.get("retrieved_context") or []
    warnings = guardrails.validate_output(sections_content, retrieved_context)
    
    # Accumulate state warnings
    state_warnings = result.get("warnings") or []
    state_warnings.extend(warnings)
    
    # 6. Build the Response Payload
    response_payload = {
        "status": result.get("status"),
        "document_type": result.get("document_type"),
        "plan": result.get("plan", []),
        "facts": result.get("facts", {}),
        "assumptions": result.get("assumptions", []),
        "data_source": result.get("data_source"),
        "sources_used": result.get("sources_used", []),
        "warnings": state_warnings,
        "rejection_reason": result.get("rejection_reason"),
        "base64_document": None
    }
    
    # Encode document to base64 if generation succeeded
    if result.get("status") in ["success", "partial_failure"]:
        doc_path = result.get("document_path", "")
        if doc_path and os.path.exists(doc_path):
            try:
                with open(doc_path, "rb") as df:
                    doc_bytes = df.read()
                    response_payload["base64_document"] = base64.b64encode(doc_bytes).decode("utf-8")
                # Clean up temporary docx file
                os.remove(doc_path)
            except Exception as read_err:
                logfire.error("Failed to read or clean up temporary docx file: {error}", error=str(read_err))
                
    # 7. Validate Response Schema Compliance
    if not guardrails.validate_response_schema(response_payload):
        logfire.error("Final response payload failed schema validation checks.")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "status": "error",
                "message": "Generated document response failed validation checks."
            }
        )
        
    return response_payload

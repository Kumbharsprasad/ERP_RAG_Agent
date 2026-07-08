from typing import TypedDict

class AgentState(TypedDict):
    user_request: str
    session_id: str
    is_business_query: bool
    rejection_reason: str
    uploaded_files: list  # list of {"filename": str, "bytes": bytes}
    parsed_chunks: list
    retrieved_context: list
    document_type: str
    plan: list
    facts: dict
    assumptions: list
    sections_content: dict
    data_source: str
    sources_used: list
    status: str
    warnings: list
    document_path: str

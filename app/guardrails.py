import re
import logfire
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class AgentAPIResponse(BaseModel):
    status: str = Field(description="The generation status, e.g. 'success' or 'rejected_non_business_query'")
    document_type: str = Field(description="The classified document category")
    plan: List[str] = Field(description="List of section headings")
    facts: Dict[str, Any] = Field(description="Key facts extracted or assumed")
    assumptions: List[str] = Field(description="List of assumptions made")
    data_source: str = Field(description="'user_upload' if uploaded files matched, else 'generated'")
    sources_used: List[Dict[str, Any]] = Field(description="List of source details (file, location, score)")
    warnings: List[str] = Field(description="List of generated warnings (e.g., PII)")
    base64_document: Optional[str] = Field(None, description="Base64-encoded Word document bytes")
    rejection_reason: Optional[str] = Field(None, description="Reason for rejection if query was off-topic")

def validate_input(request_text: str) -> tuple[bool, str]:
    """
    Validates user request text length and guards against obvious prompt injection patterns.
    """
    if not request_text or not request_text.strip():
        return False, "Request text cannot be empty."
        
    if len(request_text) > 2000:
        return False, "Request text is too long (maximum 2000 characters)."
        
    injection_patterns = [
        r"ignore\s+(?:previous|the\s+above)?\s*instructions",
        r"reveal\s+(?:your|the)?\s*system\s*prompt",
        r"reveal\s+instructions",
        r"system\s+prompt\s+override",
        r"you\s+must\s+forget",
        r"ignore\s+all\s+rules",
        r"disable\s+safety\s+checks"
    ]
    
    for pattern in injection_patterns:
        if re.search(pattern, request_text, re.IGNORECASE):
            return False, "Potential prompt injection attempt detected."
            
    return True, ""

def validate_output(sections_content: dict, retrieved_context: list) -> list[str]:
    """
    Scans generated text for PII patterns that were NOT present in the retrieved context.
    Returns a list of warning strings.
    """
    # Extract allowed PII present in the retrieved context
    context_text = "\n".join([c.get("text", "") for c in retrieved_context])
    allowed_emails = set(re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', context_text))
    allowed_phones = set(re.findall(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', context_text))
    allowed_ssns = set(re.findall(r'\b\d{3}-\d{2}-\d{4}\b', context_text))
    
    warnings = []
    
    # Scan generated sections content for new PII leakages
    for section_name, text in sections_content.items():
        emails = set(re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text))
        phones = set(re.findall(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', text))
        ssns = set(re.findall(r'\b\d{3}-\d{2}-\d{4}\b', text))
        
        new_emails = emails - allowed_emails
        new_phones = phones - allowed_phones
        new_ssns = ssns - allowed_ssns
        
        for email in new_emails:
            warnings.append(f"PII Leak Warning in section '{section_name}': Detected new email '{email}' that was not present in context.")
        for phone in new_phones:
            warnings.append(f"PII Leak Warning in section '{section_name}': Detected new phone number '{phone}' that was not present in context.")
        for ssn in new_ssns:
            warnings.append(f"PII Leak Warning in section '{section_name}': Detected new SSN '{ssn}' that was not present in context.")
            
    return warnings

def validate_response_schema(response_dict: dict) -> bool:
    """
    Confirms the final API response schema compliance using Pydantic model validation.
    """
    try:
        AgentAPIResponse(**response_dict)
        return True
    except Exception as e:
        logfire.error("Response validation failed: {error}", error=str(e))
        return False

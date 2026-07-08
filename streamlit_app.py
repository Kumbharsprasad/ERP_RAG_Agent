import os
import streamlit as st
import requests
import base64
import pandas as pd
import time

# Configure page metadata
st.set_page_config(
    page_title="Autonomous Document Generator Agent",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Backend API Configuration
BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")

# Premium UI Header Styling
st.markdown("""
    <style>
        .main-title {
            font-size: 3rem !important;
            font-weight: 800 !important;
            background: linear-gradient(45deg, #1E88E5, #D81B60);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }
        .subtitle {
            color: #6C757D;
            font-size: 1.25rem;
            margin-bottom: 2rem;
        }
        .badge-blue {
            background-color: #1E88E5;
            color: white;
            padding: 5px 12px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 14px;
            display: inline-block;
            margin-right: 10px;
            box-shadow: 0 2px 4px rgba(30,136,229,0.2);
        }
        .badge-green {
            background-color: #2E7D32;
            color: white;
            padding: 5px 12px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 14px;
            display: inline-block;
            box-shadow: 0 2px 4px rgba(46,125,50,0.2);
        }
        .badge-grey {
            background-color: #616161;
            color: white;
            padding: 5px 12px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 14px;
            display: inline-block;
            box-shadow: 0 2px 4px rgba(97,97,97,0.2);
        }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">Autonomous ERP Business Document Generator Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Generate professional, grounded enterprise documents using LangGraph RAG workflows and safety guardrails.</div>', unsafe_allow_html=True)

# Session State for Pre-filling Examples
if "prompt_input" not in st.session_state:
    st.session_state.prompt_input = ""

# Sidebar Preset Request Buttons
st.sidebar.title("Example Requests")
st.sidebar.write("Click any button below to pre-fill the generation request:")

preset_1 = "Draft a Standard Operating Procedure (SOP) for PCCOE leave application process"
preset_2 = "Tell me about the general policies of the institute."
preset_3 = "Draft a business report summarizing the people strategy themes based on my uploaded PPTX slide presentation."
preset_4 = "Who is virat kohali and what does he do"
preset_5 = "what is the capital of india write a essay on it"

if st.sidebar.button("📝 Standard SOP Request"):
    st.session_state.prompt_input = preset_1
    st.rerun()

if st.sidebar.button("❓ General Information Request"):
    st.session_state.prompt_input = preset_2
    st.rerun()

if st.sidebar.button("📊 File-Grounded Report Request"):
    st.session_state.prompt_input = preset_3
    st.rerun()

if st.sidebar.button("💪 Famous Person Request"):
    st.session_state.prompt_input = preset_4
    st.rerun()

if st.sidebar.button("📝 Essay Request"):
    st.session_state.prompt_input = preset_5
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Active View")

# Define active view in session state
if "active_view" not in st.session_state:
    st.session_state.active_view = "generator"

if st.sidebar.button("📝 Document Generator", use_container_width=True):
    st.session_state.active_view = "generator"
    st.rerun()

if st.sidebar.button("📖 Project Overview", use_container_width=True):
    st.session_state.active_view = "overview"
    st.rerun()

if st.sidebar.button("⚡ Core Capabilities & Diagrams", use_container_width=True):
    st.session_state.active_view = "capabilities"
    st.rerun()

if st.sidebar.button("🛠️ Tech Stack & Architecture", use_container_width=True):
    st.session_state.active_view = "techstack"
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.write("**Backend Server:**")
st.sidebar.code(BACKEND_API_URL)

# Route views
if st.session_state.active_view != "generator":
    if st.session_state.active_view == "overview":
        st.markdown("## Autonomous ERP Business Document Generator Agent")
        st.markdown("### What Problem It Solves")
        st.write(
            "In modern enterprise resource planning (ERP) environments, compiling standard business documents "
            "(such as SOPs, audit reports, proposals, and policies) manually is highly time-consuming, requiring "
            "synthesizing data scattered across legacy file structures, CSV spreadsheets, and PDF documents. "
            "General-purpose generative AI models fail here because they hallucinate names, dates, and compliance numbers "
            "when they lack explicit details, leading to data inaccuracy. "
            "This system solves this by forcing a strict grounding order: User Uploaded Documents > Vector Retrieved Context > "
            "Explicit Declarative Assumptions. Hallucinations are eliminated, and every generated statement is fully traceable."
        )
        st.markdown("### What we built")
        st.write("An enterprise-grade, agentic document-generation system that goes beyond simple prompt-to-docx generation. Instead of trusting an LLM to invent facts, the agent grounds every generated document in the user's own uploaded data first, falls back to reasoned assumptions only when necessary, and produces a fully traceable Word document — complete with a 'Sources & References' section showing exactly which file, page, or row informed each part of the output.")
        st.markdown("### Why this design")
        st.write("Real business systems shouldn't let an LLM hallucinate client names, dates, or figures. This architecture enforces a strict grounding hierarchy — uploaded data > retrieved context > declared assumptions — and makes that hierarchy visible in every response, rather than presenting AI-generated prose as if it were verified fact. Combined with session-scoped storage (no permanent retention of uploaded files or their embeddings) and full pipeline tracing, this is a genuinely defensible design for handling real company documents rather than just a demo.")

    elif st.session_state.active_view == "capabilities":
        st.markdown("## Core Capabilities & Diagrams")
        st.write("""
        - **Multi-format ingestion**: PDF, DOCX, PPTX, HTML, CSV, and TXT files are parsed entirely in-memory (no disk writes) using format-specific parsers, preserving precise source metadata (page number, slide number, row range, paragraph block) on every extracted chunk.
        - **Token-aware chunking**: Text is split into ~300–500 token chunks with 15% overlap, with row-boundary awareness for tabular data so no row is ever split mid-record.
        - **Session-isolated RAG**: Embeddings (Gemini text-embedding-004) are stored in Qdrant tagged by a per-session ID, with strict metadata filtering ensuring one user's uploaded data is never retrievable in another session, plus automatic cleanup of stale session vectors.
        - **Agentic orchestration via LangGraph**: A StateGraph governs the full pipeline — validating intent, checking for uploaded files, parsing, embedding, retrieving context, classifying document type, planning section structure, generating each section, and assembling the final file — with conditional routing rather than hardcoded linear logic.
        - **LLM gateway**: Groq (llama-3.1-8b-instant) handles generation while Gemini handles embeddings, both routed through a single retry/backoff-hardened gateway layer.
        - **Guardrails**: Input validation (length limits, prompt-injection keyword detection), output validation (PII leakage scanning), and schema compliance checks before any response leaves the system.
        - **Full observability**: Every LangGraph node and FastAPI request is traced via Logfire, giving node-level visibility into latency, inputs/outputs, and failures without manual print-statement debugging.
        - **Streamlit frontend**: A clean, step-tracked UI showing the agent's live progress, document type classification, data source used (uploaded file vs. generated), and a downloadable final document.
        """)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("### Systems Architecture Diagram")
            st.image("enterprise_rag_agent_architecture.png", use_container_width=True)
        with col2:
            st.markdown("### Pipeline Workflow Diagram")
            st.image("workflow_diagram.png", use_container_width=True)

    elif st.session_state.active_view == "techstack":
        st.markdown("## Tech Stack Components")
        tech_data = {
            "Layer": [
                "Orchestration", "Backend API", "Frontend", 
                "Generation LLM", "Embedding model", "LLM routing/gateway", 
                "Vector database", "Observability", "Guardrails", 
                "Document assembly", "File parsing", "Deployment"
            ],
            "Technology": [
                "LangGraph (StateGraph, conditional edges)", "FastAPI", "Streamlit",
                "Groq — Llama 3.1 8B Instant", "Gemini text-embedding-004", "LiteLLM",
                "Qdrant Cloud (session-scoped, metadata-filtered)", "Pydantic Logfire (OpenTelemetry-based tracing)", 
                "Guardrails AI + custom regex-based PII/injection checks",
                "python-docx", "pdfplumber, python-docx, python-pptx, BeautifulSoup, pandas", 
                "FastAPI on Render, Streamlit on Streamlit Community Cloud"
            ]
        }
        df = pd.DataFrame(tech_data)
        st.table(df)
    st.stop()

# Main Form Elements
request_prompt = st.text_area(
    "What document would you like to generate?",
    value=st.session_state.prompt_input,
    placeholder="Type your generation prompt here (e.g., 'Draft a Standard Operating Procedure for ...')",
    height=150
)

uploaded_files = st.file_uploader(
    "Upload supporting documents (Optional - Max 5 files, 10MB each)",
    type=["pdf", "docx", "pptx", "html", "csv", "txt"],
    accept_multiple_files=True
)

if st.button("Generate Document", type="primary"):
    if not request_prompt.strip():
        st.error("Please enter a valid request prompt before generating.")
    else:
        # Prepare parameters and files dictionary for request
        payload = {"request": request_prompt}
        files_data = []
        
        # Open and process files if present
        file_handling_error = False
        if uploaded_files:
            if len(uploaded_files) > 5:
                st.error("You can only upload a maximum of 5 files.")
                file_handling_error = True
            else:
                for uf in uploaded_files:
                    files_data.append(("files", (uf.name, uf.read(), uf.type)))
        
        if not file_handling_error:
            # Call backend API
            try:
                # 1. Start Visual Step Tracker
                with st.status("Starting document generation agent...", expanded=True) as status_box:
                    st.write("⏳ Validating request prompt...")
                    time.sleep(0.3)
                    
                    if uploaded_files:
                        st.write("⏳ Validating uploaded files metadata...")
                        time.sleep(0.3)
                        
                    st.write("⏳ Dispatching request to LangGraph orchestrator...")
                    
                    # API POST call
                    response = requests.post(
                        f"{BACKEND_API_URL}/agent",
                        data=payload,
                        files=files_data if files_data else None,
                        timeout=300  # Give it ample time for large LLM runs
                    )
                    
                    # Check responses
                    if response.status_code == 200:
                        data = response.json()
                        status_box.update(label="Document generation complete!", state="complete")
                    elif response.status_code == 400:
                        detail = response.json().get("detail", "Input validation rejected.")
                        status_box.update(label="Input validation failed.", state="error")
                        st.error(f"Validation Error: {detail}")
                        st.stop()
                    else:
                        status_box.update(label="Generation pipeline encountered an error.", state="error")
                        st.error(f"Error ({response.status_code}): {response.text}")
                        st.stop()
                
                # 2. Extract Response Fields
                status = data.get("status")
                doc_type = data.get("document_type", "Other")
                plan = data.get("plan", [])
                facts = data.get("facts", {})
                assumptions = data.get("assumptions", [])
                data_source = data.get("data_source", "generated")
                sources_used = data.get("sources_used", [])
                warnings = data.get("warnings", [])
                base64_doc = data.get("base64_document")
                rejection_reason = data.get("rejection_reason")
                
                # 3. Handle Intent Rejection Node Response
                if status == "rejected_non_business_query":
                    st.warning("⚠️ Request rejected by Intent Guardrail")
                    st.info(f"**Reason:** {rejection_reason}")
                    st.stop()
                    
                # 4. Display Results Page
                st.success("✨ Document successfully compiled!")
                
                # Badges row
                badge_html = f'<div class="badge-blue">Category: {doc_type}</div>'
                if data_source == "user_upload":
                    badge_html += '<div class="badge-green">Data Source: User Uploads (RAG)</div>'
                else:
                    badge_html += '<div class="badge-grey">Data Source: Synthesized</div>'
                
                st.markdown(badge_html, unsafe_allow_html=True)
                st.write("") # Spacer
                
                # Main download button
                if base64_doc:
                    doc_bytes = base64.b64decode(base64_doc)
                    filename = f"{doc_type.lower().replace(' ', '_')}_generated.docx"
                    st.download_button(
                        label="💾 Download Generated Word Document (.docx)",
                        data=doc_bytes,
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True
                    )
                
                # Warnings Section
                if warnings:
                    st.write("---")
                    st.subheader("⚠️ Guardrail Warnings")
                    for w in warnings:
                        st.warning(w)
                
                # Metadata / Structure Accordions
                st.write("---")
                col1, col2 = st.columns(2)
                
                with col1:
                    with st.expander("📋 Document Structural Plan Outline", expanded=True):
                        if plan:
                            for idx, sec in enumerate(plan, 1):
                                st.write(f"**{idx}. {sec}**")
                        else:
                            st.write("*No structural plan returned.*")
                            
                    if assumptions:
                        with st.expander("🛠️ Assumptions Made", expanded=True):
                            for asn in assumptions:
                                st.warning(f"• {asn}")
                                
                with col2:
                    with st.expander("💡 Extracted Key Facts & Details", expanded=True):
                        if facts:
                            for k, v in facts.items():
                                st.write(f"**{k}:** {v}")
                        else:
                            st.write("*No facts extracted.*")
                            
                    if data_source == "user_upload" and sources_used:
                        with st.expander("📚 Sources & References Grounding", expanded=True):
                            ref_df = pd.DataFrame(sources_used)
                            # Format columns for display
                            if not ref_df.empty:
                                ref_df.columns = ["Source File", "Location", "Similarity Score"]
                                st.dataframe(ref_df, use_container_width=True)
                            else:
                                st.write("*No referencing sources parsed.*")
                                
            except Exception as conn_err:
                st.error(f"Failed to connect to backend server: {str(conn_err)}")

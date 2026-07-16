"use client";

import React, { useState, useEffect } from "react";
import RequestForm from "../components/RequestForm";
import WorkflowStatus from "../components/WorkflowStatus";
import ResultPanel from "../components/ResultPanel";
import { generateDocument, GenerationResponse } from "../lib/api";
import {
  AlertCircle,
  ArrowDown,
  Layers,
  Shield,
  Activity,
  Zap,
  RotateCcw,
  Sparkles,
  BookOpen
} from "lucide-react";

export default function DocumentGenerator() {
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error" | "partial_failure" | "rejected">("idle");
  const [response, setResponse] = useState<GenerationResponse | null>(null);
  const [activeStep, setActiveStep] = useState(-1);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [activeSection, setActiveSection] = useState("hero");

  // Track active section via IntersectionObserver
  useEffect(() => {
    const sections = ["hero", "capabilities", "workflow", "safety", "dashboard"];
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveSection(entry.target.id);
          }
        });
      },
      { threshold: 0.25 }
    );

    sections.forEach((id) => {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    });

    return () => {
      sections.forEach((id) => {
        const el = document.getElementById(id);
        if (el) observer.unobserve(el);
      });
    };
  }, []);

  // Update workflow steps during active generation
  useEffect(() => {
    if (!isLoading) return;

    const timers: NodeJS.Timeout[] = [];
    const advanceStep = (delay: number, step: number) => {
      timers.push(
        setTimeout(() => {
          setActiveStep(step);
        }, delay)
      );
    };

    // Simulated node transition triggers matching graph flow
    advanceStep(0, 0);       // Validation
    advanceStep(2000, 1);    // Parsing
    advanceStep(5500, 2);    // Embedding & Retrieval
    advanceStep(9000, 3);    // Classification
    advanceStep(12000, 4);   // Planning
    advanceStep(15000, 5);   // Generation
    advanceStep(22000, 6);   // Assembly

    return () => {
      timers.forEach(clearTimeout);
    };
  }, [isLoading]);

  const handleSubmit = async (requestText: string, files: File[]) => {
    setIsLoading(true);
    setStatus("loading");
    setResponse(null);
    setErrorMessage(null);
    setActiveStep(0);

    // Smooth scroll down to dashboard immediately so user sees progress
    document.getElementById("dashboard")?.scrollIntoView({ behavior: "smooth" });

    try {
      const res = await generateDocument(requestText, files);

      if (res.status === "rejected_non_business_query") {
        setStatus("rejected");
        setActiveStep(-1);
      } else if (res.status === "partial_failure") {
        setStatus("partial_failure");
        setActiveStep(6);
      } else {
        setStatus("success");
        setActiveStep(6);
      }

      setResponse(res);
    } catch (err: any) {
      console.error(err);
      setStatus("error");
      setErrorMessage(err.message || "Failed to establish a connection to the backend server.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setStatus("idle");
    setResponse(null);
    setActiveStep(-1);
    setErrorMessage(null);
    document.getElementById("dashboard")?.scrollIntoView({ behavior: "smooth" });
  };

  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <div className="relative min-h-screen font-sans antialiased text-slate-800 bg-slate-50 selection:bg-indigo-100">
      
      {/* Floating Side Navigation Dot Tracker */}
      <nav className="fixed right-6 top-1/2 -translate-y-1/2 z-50 hidden md:flex flex-col gap-4 p-3 bg-white/60 backdrop-blur-md border border-indigo-100/50 rounded-full shadow-lg">
        {["hero", "capabilities", "workflow", "safety", "dashboard"].map((id) => (
          <button
            key={id}
            onClick={() => scrollTo(id)}
            className={`w-3.5 h-3.5 rounded-full transition-all duration-300 relative group cursor-pointer`}
          >
            <span
              className={`absolute inset-0 rounded-full transition-all duration-300 ${
                activeSection === id ? "bg-indigo-600 scale-100" : "bg-slate-300 scale-75 group-hover:bg-slate-400"
              }`}
            />
            {/* Tooltip */}
            <span className="absolute right-6 top-1/2 -translate-y-1/2 px-2.5 py-1 rounded bg-slate-800 text-[10px] text-white font-mono opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none capitalize">
              {id === "hero" ? "Intro" : id}
            </span>
          </button>
        ))}
      </nav>

      {/* Floating Rounded-Full Transparent Header */}
      <header className="fixed top-4 left-1/2 -translate-x-1/2 w-[92%] max-w-5xl z-50 glass-panel rounded-full px-6 py-3 flex items-center justify-between border border-indigo-200 shadow-lg">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-indigo-600 animate-pulse" />
          <h1 className="text-sm font-black tracking-tight text-slate-900">
            <span className="bg-gradient-to-r from-indigo-600 to-teal-600 bg-clip-text text-transparent">
              ERP RAG
            </span>{" "}
            Document Agent
          </h1>
        </div>
        <div className="flex items-center gap-6">
          <nav className="hidden sm:flex items-center gap-5 text-xs font-semibold text-slate-600">
            <button onClick={() => scrollTo("capabilities")} className="hover:text-indigo-600 transition-colors cursor-pointer">Capabilities</button>
            <button onClick={() => scrollTo("workflow")} className="hover:text-indigo-600 transition-colors cursor-pointer">Pipeline</button>
            <button onClick={() => scrollTo("safety")} className="hover:text-indigo-600 transition-colors cursor-pointer">Observability</button>
          </nav>
          {status !== "idle" && (
            <button
              onClick={handleReset}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold text-slate-600 bg-white/80 border border-slate-200 hover:bg-slate-50 transition-all cursor-pointer"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Reset
            </button>
          )}
        </div>
      </header>

      {/* ──────────────────────────────────────────────────────── */}
      {/* SECTION 1: HERO & INTRODUCTION */}
      {/* ──────────────────────────────────────────────────────── */}
      <section
        id="hero"
        className="min-screen-fold min-h-screen flex flex-col justify-between items-center px-4 pt-28 pb-12 sm:px-6 lg:px-8 bg-gradient-to-b from-white to-slate-50 relative overflow-hidden"
      >
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#8080800a_1px,transparent_1px),linear-gradient(to_bottom,#8080800a_1px,transparent_1px)] bg-[size:14px_24px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] pointer-events-none" />
        
        <div /> {/* spacing */}

        <div className="max-w-4xl text-center space-y-6 z-10">
          <h2 className="text-4xl sm:text-6xl font-black text-slate-900 leading-tight tracking-tight">
            Autonomous Business <br />
            <span className="bg-gradient-to-r from-indigo-600 to-teal-500 bg-clip-text text-transparent">
              Document RAG Agent
            </span>
          </h2>
          
          <p className="max-w-2xl mx-auto text-sm sm:text-base text-slate-600 leading-relaxed font-medium">
            Generate layout-aware, context-grounded enterprise documents in Microsoft Word formats automatically. 
            Powered by LangGraph multi-node state machines, Qdrant vector retrieval, and telemetry diagnostics.
          </p>

          <div className="pt-4 flex items-center justify-center gap-4">
            <button
              onClick={() => scrollTo("dashboard")}
              className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-sm rounded-xl shadow-md shadow-indigo-600/10 hover:shadow-indigo-600/20 transition-all hover:scale-[1.02] cursor-pointer"
            >
              Launch Generator Workspace
            </button>
            <button
              onClick={() => scrollTo("capabilities")}
              className="px-6 py-3 bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 font-bold text-sm rounded-xl transition-all cursor-pointer"
            >
              Learn Core Pipeline
            </button>
          </div>
        </div>

        {/* Scroll Indicator */}
        <div className="flex flex-col items-center gap-2 cursor-pointer z-10 opacity-70 hover:opacity-100 transition-opacity" onClick={() => scrollTo("capabilities")}>
          <span className="text-[10px] font-mono font-bold tracking-wider text-slate-500 uppercase">
            Explore Capabilities
          </span>
          <div className="p-2 rounded-full border border-slate-200 bg-white shadow-sm animate-bounce-down">
            <ArrowDown className="w-4 h-4 text-indigo-600" />
          </div>
        </div>
      </section>

      {/* ──────────────────────────────────────────────────────── */}
      {/* SECTION 2: KEY CAPABILITIES */}
      {/* ──────────────────────────────────────────────────────── */}
      <section
        id="capabilities"
        className="min-h-screen flex flex-col justify-center px-4 py-20 sm:px-6 lg:px-8 bg-white border-y border-slate-100 relative"
      >
        <div className="max-w-7xl mx-auto space-y-12 w-full">
          <div className="text-center space-y-3">
            <h3 className="text-xs font-mono uppercase tracking-wider text-indigo-600 font-bold">
              Product Capabilities
            </h3>
            <h2 className="text-3xl font-black text-slate-900 tracking-tight">
              Enterprise Grounded Writing Agent
            </h2>
            <p className="max-w-2xl mx-auto text-xs sm:text-sm text-slate-500 font-medium">
              The agent integrates file parsing, vector databases, and LLM planning to guarantee structural compliance and accuracy.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="p-6 rounded-2xl border border-slate-100 bg-slate-50/50 hover:bg-white hover:border-indigo-200 hover:shadow-lg transition-all duration-300 group">
              <div className="w-10 h-10 rounded-xl bg-indigo-50 flex items-center justify-center text-indigo-600 mb-4 group-hover:scale-110 transition-transform">
                <Layers className="w-5 h-5" />
              </div>
              <h4 className="text-sm font-bold text-slate-900 mb-2">Layout-Aware Parser</h4>
              <p className="text-xs text-slate-500 leading-relaxed font-medium">
                LiteParse consolidation converts PDFs, Word DOCX, spreadsheets XLSX, and images (PNG/JPG) directly into Markdown structure, retaining layouts and tables.
              </p>
            </div>

            <div className="p-6 rounded-2xl border border-slate-100 bg-slate-50/50 hover:bg-white hover:border-indigo-200 hover:shadow-lg transition-all duration-300 group">
              <div className="w-10 h-10 rounded-xl bg-indigo-50 flex items-center justify-center text-indigo-600 mb-4 group-hover:scale-110 transition-transform">
                <Zap className="w-5 h-5" />
              </div>
              <h4 className="text-sm font-bold text-slate-900 mb-2">Qdrant In-Memory RAG</h4>
              <p className="text-xs text-slate-500 leading-relaxed font-medium">
                Loads and indexes chunks with Gemini 3072-dim embeddings. Features session isolation tags and TTL automated sweeps to keep workspace memory clean.
              </p>
            </div>

            <div className="p-6 rounded-2xl border border-slate-100 bg-slate-50/50 hover:bg-white hover:border-indigo-200 hover:shadow-lg transition-all duration-300 group">
              <div className="w-10 h-10 rounded-xl bg-indigo-50 flex items-center justify-center text-indigo-600 mb-4 group-hover:scale-110 transition-transform">
                <Shield className="w-5 h-5" />
              </div>
              <h4 className="text-sm font-bold text-slate-900 mb-2">PII & Injection Guards</h4>
              <p className="text-xs text-slate-500 leading-relaxed font-medium">
                Blocks overrides and scans generated paragraph text client-side to flag newly introduced emails, phone numbers, or SSNs.
              </p>
            </div>

            <div className="p-6 rounded-2xl border border-slate-100 bg-slate-50/50 hover:bg-white hover:border-indigo-200 hover:shadow-lg transition-all duration-300 group">
              <div className="w-10 h-10 rounded-xl bg-indigo-50 flex items-center justify-center text-indigo-600 mb-4 group-hover:scale-110 transition-transform">
                <Activity className="w-5 h-5" />
              </div>
              <h4 className="text-sm font-bold text-slate-900 mb-2">Logfire Telemetry Trace</h4>
              <p className="text-xs text-slate-500 leading-relaxed font-medium">
                Features deep server-side observability using Pydantic Logfire, tracking every node transition, API request latency, and warning signal.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ──────────────────────────────────────────────────────── */}
      {/* SECTION 3: RAG INGESTION PIPELINE */}
      {/* ──────────────────────────────────────────────────────── */}
      <section
        id="workflow"
        className="min-h-screen flex flex-col justify-center px-4 py-20 sm:px-6 lg:px-8 bg-slate-50 relative"
      >
        <div className="max-w-7xl mx-auto space-y-12 w-full">
          <div className="text-center space-y-3">
            <h3 className="text-xs font-mono uppercase tracking-wider text-indigo-600 font-bold">
              System Pipeline
            </h3>
            <h2 className="text-3xl font-black text-slate-900 tracking-tight">
              4-Stage Ingestion & Assembly Flow
            </h2>
            <p className="max-w-2xl mx-auto text-xs sm:text-sm text-slate-500 font-medium">
              How the LangGraph RAG Agent processes user input files and drafts MS Word files.
            </p>
          </div>

          <div className="relative border border-slate-200/60 bg-white rounded-2xl p-6 sm:p-10 shadow-md">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-8 relative">
              
              <div className="space-y-3">
                <div className="w-8 h-8 rounded-full bg-indigo-600 text-white font-bold font-mono text-xs flex items-center justify-center">
                  1
                </div>
                <h4 className="text-sm font-bold text-slate-900">In-Memory Parsing</h4>
                <p className="text-[11px] text-slate-500 leading-relaxed font-medium">
                  Bytes are read directly using `io.BytesIO`. LiteParse processes PDF/DOCX layouts, running local Tesseract auto-OCR if pages contain sparse text.
                </p>
              </div>

              <div className="space-y-3">
                <div className="w-8 h-8 rounded-full bg-indigo-600 text-white font-bold font-mono text-xs flex items-center justify-center">
                  2
                </div>
                <h4 className="text-sm font-bold text-slate-900">Vector Isolation</h4>
                <p className="text-[11px] text-slate-500 leading-relaxed font-medium">
                  Splits text into sliding windows. Computes 3072-dimension Gemini vectors and indexes them into Qdrant Cloud. TTL sweeps clear expired session indices.
                </p>
              </div>

              <div className="space-y-3">
                <div className="w-8 h-8 rounded-full bg-indigo-600 text-white font-bold font-mono text-xs flex items-center justify-center">
                  3
                </div>
                <h4 className="text-sm font-bold text-slate-900">Graph Drafting Loop</h4>
                <p className="text-[11px] text-slate-500 leading-relaxed font-medium">
                  FastAPI triggers LangGraph. Evaluates intents, classifies category, drafts layout map, retrieves context, and dynamically writes each section.
                </p>
              </div>

              <div className="space-y-3">
                <div className="w-8 h-8 rounded-full bg-indigo-600 text-white font-bold font-mono text-xs flex items-center justify-center">
                  4
                </div>
                <h4 className="text-sm font-bold text-slate-900">Word Assembly</h4>
                <p className="text-[11px] text-slate-500 leading-relaxed font-medium">
                  Compiles paragraphs, explicit assumptions, variables metadata, and vector sources directly into MS Word XML blocks, serving raw base64 data.
                </p>
              </div>
              
            </div>
          </div>
        </div>
      </section>

      {/* ──────────────────────────────────────────────────────── */}
      {/* SECTION 4: SAFETY & OBSERVABILITY */}
      {/* ──────────────────────────────────────────────────────── */}
      <section
        id="safety"
        className="min-h-screen flex flex-col justify-center px-4 py-20 sm:px-6 lg:px-8 bg-white relative"
      >
        <div className="max-w-7xl mx-auto space-y-12 w-full">
          <div className="text-center space-y-3">
            <h3 className="text-xs font-mono uppercase tracking-wider text-indigo-600 font-bold">
              Observability & Safety
            </h3>
            <h2 className="text-3xl font-black text-slate-900 tracking-tight">
              Safety Guardrails & Logfire Traces
            </h2>
            <p className="max-w-2xl mx-auto text-xs sm:text-sm text-slate-500 font-medium">
              The agent maintains rigorous check-points to ensure safety and data leakage compliance.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
            {/* Visual description */}
            <div className="space-y-6">
              <div className="space-y-2">
                <h4 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <Shield className="w-5 h-5 text-indigo-600" />
                  PII Scanning & Safety Filters
                </h4>
                <p className="text-xs text-slate-500 leading-relaxed font-medium">
                  The API scans generated content using PII indicators (emails, phones, SSNs) and matches against context retrieved from Qdrant. If new variables are introduced, warnings are appended. Prompt overrides are auto-blocked.
                </p>
              </div>

              <div className="space-y-2">
                <h4 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <Activity className="w-5 h-5 text-indigo-600" />
                  Logfire Cloud Traces Dashboard
                </h4>
                <p className="text-xs text-slate-500 leading-relaxed font-medium">
                  Integrates with OpenTelemetry trace exporters to project latency spans directly to Logfire, allowing real-time audit control over API calls and retry limits.
                </p>
              </div>
            </div>

            {/* Simulated telemetry panel */}
            <div className="p-6 rounded-2xl border border-slate-200 bg-slate-950 text-slate-400 font-mono text-[10px] space-y-3 shadow-md">
              <div className="flex items-center justify-between pb-2 border-b border-slate-800 text-slate-500">
                <span className="font-bold">LOGFIRE MONITORING TRACE</span>
                <span>Active</span>
              </div>
              <div className="space-y-1">
                <div className="text-slate-500">23:24:42.379 [INFO] fastapi.request GET /health - Status 200</div>
                <div className="text-indigo-400">23:24:44.467 [SPAN] execute_graph_node "intent_guard" elapsed=420ms</div>
                <div className="text-cyan-400">23:24:45.809 [SPAN] execute_graph_node "parser" elapsed=1200ms</div>
                <div className="text-blue-400">23:24:46.825 [DB] qdrant.upsert_points session_id=session_alice_123 - 2 points</div>
                <div className="text-purple-400">23:24:49.227 [WARNING] pii_scan: Detected SSN warning in section "Employee Details"</div>
                <div className="text-emerald-400 font-bold">23:24:51.016 [SUCCESS] graph.execute_workflow - assembled_docx compiler completed.</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ──────────────────────────────────────────────────────── */}
      {/* SECTION 5: INTERACTIVE GENERATION WORKSPACE (DASHBOARD) */}
      {/* ──────────────────────────────────────────────────────── */}
      <section
        id="dashboard"
        className="min-h-screen flex flex-col justify-center px-4 py-20 sm:px-6 lg:px-8 bg-slate-50 relative border-t border-slate-100"
      >
        <div className="max-w-7xl mx-auto space-y-12 w-full">
          <div className="text-center space-y-3">
            <h3 className="text-xs font-mono uppercase tracking-wider text-indigo-600 font-bold">
              Interactive Workspace
            </h3>
            <h2 className="text-3xl font-black text-slate-900 tracking-tight">
              Document Generation Dashboard
            </h2>
            <p className="max-w-2xl mx-auto text-xs sm:text-sm text-slate-500 font-medium">
              Configure parameters, upload context documents, monitor compiler pipeline step checks, and download generated assets below.
            </p>
          </div>

          {/* Generator Interface Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            {/* Left Column: Form Controls */}
            <div className="lg:col-span-7 glass-panel p-6 rounded-2xl space-y-6">
              <h3 className="text-sm font-bold text-slate-900 pb-3 border-b border-slate-100 flex items-center gap-1.5">
                <BookOpen className="w-4.5 h-4.5 text-indigo-600" />
                Configure Request Parameters
              </h3>
              <RequestForm onSubmit={handleSubmit} isLoading={isLoading} />
            </div>

            {/* Right Column: Status steps */}
            <div className="lg:col-span-5">
              <WorkflowStatus
                activeStep={activeStep}
                isCompleted={status === "success" || status === "partial_failure"}
                isFailed={status === "error" || status === "rejected"}
              />
            </div>
          </div>

          {/* Generation Error Alerts */}
          {status === "error" && errorMessage && (
            <div className="glass-panel p-6 rounded-2xl border border-red-200 bg-red-50 text-red-800 shadow-sm">
              <div className="flex items-center gap-2 font-bold text-red-600 mb-2">
                <AlertCircle className="w-5 h-5 flex-shrink-0" />
                System Generation Failure
              </div>
              <p className="text-xs text-red-900/90 font-medium leading-relaxed">{errorMessage}</p>
            </div>
          )}

          {/* Results Download Panel */}
          {response && (
            <div className="mt-8">
              <ResultPanel response={response} />
            </div>
          )}
        </div>
      </section>

      {/* Footer Branding */}
      <footer className="bg-white border-t border-slate-100 py-8 px-4 text-center text-[10px] text-slate-500 font-mono space-y-2">
        <div>
          ERP_RAG_AGENT • SECURED LOGFIRE ENVIRONMENT • POWERED BY NEXT.JS & FASTAPI
        </div>
        <div className="text-slate-400">
          Developed by{" "}
          <a
            href="https://www.linkedin.com/in/prasad-kumbhar23/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-indigo-600 hover:text-indigo-700 hover:underline font-bold transition-all"
          >
            Prasad Kumbhar
          </a>
        </div>
      </footer>
    </div>
  );
}

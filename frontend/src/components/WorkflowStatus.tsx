import React from "react";
import { CheckCircle2, Circle, Loader2 } from "lucide-react";

interface WorkflowStatusProps {
  activeStep: number; // 0 to 6 representing current step, -1 if not started
  isCompleted: boolean;
  isFailed: boolean;
}

const STEPS = [
  { title: "Request Validation", desc: "Verifying input parameters and injection guardrails" },
  { title: "File Ingestion", desc: "Consolidating formats (PDF, DOCX, XLSX, Images) in-memory" },
  { title: "Embedding & Retrieval", desc: "Generating vector weights and retrieving context" },
  { title: "Document Classification", desc: "Inferring target category and matching templates" },
  { title: "Document Layout Planning", desc: "Constructing outline headings and fact states" },
  { title: "Section Content Generation", desc: "Dynamic section composition and grounding checks" },
  { title: "Document Assembly", desc: "Compiling paragraph styles into final Word document" },
];

export default function WorkflowStatus({ activeStep, isCompleted, isFailed }: WorkflowStatusProps) {
  return (
    <div className="glass-panel p-6 rounded-2xl space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <h3 className="text-sm font-semibold text-slate-800">Agent Processing Progress</h3>
        {activeStep >= 0 && !isCompleted && !isFailed && (
          <span className="flex items-center gap-1 text-[10px] font-mono font-bold text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-100">
            <Loader2 className="w-3 h-3 animate-spin" />
            PROCESSING
          </span>
        )}
      </div>

      <div className="relative pl-6 space-y-5 before:absolute before:left-2.5 before:top-2 before:bottom-2 before:w-0.5 before:bg-slate-200">
        {STEPS.map((step, idx) => {
          let state: "pending" | "active" | "done" | "failed" = "pending";
          
          if (isFailed && idx === activeStep) {
            state = "failed";
          } else if (isCompleted) {
            state = "done";
          } else if (activeStep > idx) {
            state = "done";
          } else if (activeStep === idx) {
            state = "active";
          }

          return (
            <div key={idx} className="relative transition-all duration-300">
              {/* Step indicator */}
              <div className="absolute -left-[27px] top-0.5 flex items-center justify-center bg-slate-50 rounded-full p-0.5">
                {state === "done" && (
                  <CheckCircle2 className="w-4.5 h-4.5 text-indigo-600 fill-indigo-50" />
                )}
                {state === "active" && (
                  <div className="w-4.5 h-4.5 rounded-full bg-indigo-50 border-2 border-indigo-600 flex items-center justify-center animate-glow-pulse">
                    <div className="w-1.5 h-1.5 rounded-full bg-indigo-600 animate-ping" />
                  </div>
                )}
                {state === "failed" && (
                  <div className="w-4.5 h-4.5 rounded-full bg-red-50 border border-red-500 flex items-center justify-center">
                    <div className="w-1.5 h-1.5 rounded-full bg-red-500" />
                  </div>
                )}
                {state === "pending" && (
                  <Circle className="w-4.5 h-4.5 text-slate-300" />
                )}
              </div>

              {/* Step content */}
              <div
                className={`transition-opacity duration-300 ${
                  state === "pending"
                    ? "opacity-35"
                    : state === "active"
                    ? "opacity-100"
                    : "opacity-90"
                }`}
              >
                <h4
                  className={`text-xs font-semibold ${
                    state === "active"
                      ? "text-indigo-600 font-bold"
                      : state === "failed"
                      ? "text-red-500 font-bold"
                      : "text-slate-800"
                  }`}
                >
                  {step.title}
                </h4>
                <p className="text-[10px] text-slate-500 mt-0.5 leading-relaxed">
                  {step.desc}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

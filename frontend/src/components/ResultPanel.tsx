import React from "react";
import { Download, FileCheck, HelpCircle, CheckSquare } from "lucide-react";
import DataSourceBadge from "./DataSourceBadge";
import WarningsPanel from "./WarningsPanel";
import SourcesTable from "./SourcesTable";
import { GenerationResponse } from "../lib/api";

interface ResultPanelProps {
  response: GenerationResponse;
}

export default function ResultPanel({ response }: ResultPanelProps) {
  const {
    status,
    document_type,
    plan,
    facts,
    assumptions,
    data_source,
    sources_used,
    warnings,
    rejection_reason,
    base64_document,
  } = response;

  const handleDownload = () => {
    if (!base64_document) return;
    try {
      const byteCharacters = atob(base64_document);
      const byteNumbers = new Array(byteCharacters.length);
      for (let i = 0; i < byteCharacters.length; i++) {
        byteNumbers[i] = byteCharacters.charCodeAt(i);
      }
      const byteArray = new Uint8Array(byteNumbers);
      const blob = new Blob([byteArray], {
        type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      const cleanName = (document_type || "Grounded").replace(/[^a-zA-Z0-9]/g, "_");
      link.download = `${cleanName}_Document.docx`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert("Error compiling document bytes.");
      console.error(err);
    }
  };

  if (status === "rejected_non_business_query") {
    return (
      <div className="glass-panel p-6 rounded-2xl border border-red-200 bg-red-50 text-red-800 shadow-md">
        <div className="flex items-center gap-2 font-bold text-red-600 mb-3 text-lg">
          <HelpCircle className="w-6 h-6 animate-pulse" />
          Request Out of Scope
        </div>
        <p className="text-sm leading-relaxed mb-4 text-red-900/90 font-medium">
          {rejection_reason || "The request was evaluated as non-business related and was rejected."}
        </p>
      </div>
    );
  }

  const isPartial = status === "partial_failure";

  return (
    <div className="glass-panel p-6 rounded-2xl space-y-6 shadow-md animate-fade-in">
      {/* Title Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
        <div>
          <span className="text-xs font-mono uppercase tracking-wider text-indigo-600 font-bold">
            Document Generation Success
          </span>
          <h2 className="text-xl font-black text-slate-800 mt-0.5 flex items-center gap-2">
            <FileCheck className="w-5.5 h-5.5 text-indigo-600" />
            {document_type || "Generated Document"}
          </h2>
        </div>
        <div className="flex items-center gap-2 self-start sm:self-auto">
          <DataSourceBadge dataSource={data_source} />
          {isPartial && (
            <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-50 text-amber-700 border border-amber-200 shadow-sm">
              Partial Success
            </span>
          )}
        </div>
      </div>

      {/* Warnings & Alerts */}
      <WarningsPanel warnings={warnings} />

      {/* Outline Plan */}
      {plan && plan.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-bold text-slate-700 flex items-center gap-1.5">
            <CheckSquare className="w-4.5 h-4.5 text-indigo-600" />
            Document Layout Outline
          </h3>
          <ol className="grid grid-cols-1 md:grid-cols-2 gap-2.5 text-xs text-slate-700 font-medium">
            {plan.map((heading, i) => (
              <li
                key={i}
                className="flex items-center gap-2.5 px-3.5 py-2.5 rounded-xl bg-slate-50 border border-slate-200/65 hover:border-indigo-300 transition-all shadow-sm"
              >
                <span className="font-mono text-indigo-600 font-black">{i + 1}.</span>
                <span className="truncate">{heading}</span>
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Assumptions Box */}
      {assumptions && assumptions.length > 0 && (
        <div className="space-y-2.5">
          <h3 className="text-sm font-bold text-slate-700">Explicit Document Assumptions</h3>
          <div className="rounded-xl border border-amber-200 bg-amber-50/50 p-4">
            <ul className="list-disc list-inside space-y-1.5 text-xs text-amber-900/90 leading-relaxed font-medium">
              {assumptions.map((asm, idx) => (
                <li key={idx}>{asm}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Facts Metadata */}
      {facts && Object.keys(facts).length > 0 && (
        <div className="space-y-2.5">
          <h3 className="text-sm font-bold text-slate-700">Extracted Facts & Variables</h3>
          <div className="rounded-xl border border-slate-200 overflow-hidden shadow-sm">
            <div className="grid grid-cols-1 sm:grid-cols-2 divide-y sm:divide-y-0 sm:divide-x divide-slate-200 text-xs">
              {Object.entries(facts).map(([key, value]) => (
                <div key={key} className="p-3.5 bg-slate-50/40 flex justify-between gap-4">
                  <span className="text-slate-500 font-semibold break-words">{key}</span>
                  <span className="text-slate-800 text-right font-mono font-bold break-all">{String(value)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Grounding Reference Table */}
      <SourcesTable sources={sources_used} />

      {/* Download Action Button */}
      {base64_document && (
        <button
          onClick={handleDownload}
          className="w-full flex items-center justify-center gap-2 px-5 py-3.5 rounded-xl font-bold text-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none transition-all shadow-[0_4px_16px_rgba(79,70,229,0.25)] hover:scale-[1.002] active:scale-[0.998] cursor-pointer"
        >
          <Download className="w-4 h-4" />
          Download Assembled Word Document (.docx)
        </button>
      )}
    </div>
  );
}

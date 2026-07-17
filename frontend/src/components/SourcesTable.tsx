import React, { useState } from "react";
import { SourceUsed } from "../lib/api";
import { ChevronDown, ChevronUp, Link } from "lucide-react";

interface SourcesTableProps {
  sources: SourceUsed[];
}

export default function SourcesTable({ sources }: SourcesTableProps) {
  const [isOpen, setIsOpen] = useState(false);

  if (!sources || sources.length === 0) return null;

  return (
    <div className="rounded-xl border border-slate-200 bg-white overflow-hidden shadow-sm transition-all duration-300">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 text-sm font-semibold hover:bg-slate-50 text-slate-800 transition-colors"
      >
        <div className="flex items-center gap-2 text-indigo-600">
          <Link className="w-4 h-4" />
          Retrieved Grounding Sources ({sources.length})
        </div>
        {isOpen ? (
          <ChevronUp className="w-4 h-4 text-slate-400" />
        ) : (
          <ChevronDown className="w-4 h-4 text-slate-400" />
        )}
      </button>

      {isOpen && (
        <div className="border-t border-slate-200 overflow-x-auto custom-scrollbar">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 text-slate-700 font-bold border-b border-slate-200">
                <th className="p-3">Source File</th>
                <th className="p-3">Location / Slide / Page</th>
                <th className="p-3 text-right">Similarity Score</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {sources.map((src, index) => (
                <tr key={index} className="hover:bg-slate-50/50 transition-colors text-slate-600">
                  <td className="p-3 font-semibold text-slate-800 break-all">{src.file}</td>
                  <td className="p-3 font-medium">{src.location || "N/A"}</td>
                  <td className="p-3 text-right font-mono font-bold text-indigo-600">
                    {(src.score || 0).toFixed(4)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

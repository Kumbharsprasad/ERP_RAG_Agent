import React from "react";
import { AlertTriangle } from "lucide-react";

interface WarningsPanelProps {
  warnings: string[];
}

export default function WarningsPanel({ warnings }: WarningsPanelProps) {
  if (!warnings || warnings.length === 0) return null;

  return (
    <div className="rounded-xl border border-amber-200 bg-amber-50/70 p-4 text-sm text-amber-800 shadow-sm leading-relaxed">
      <div className="flex items-center gap-2 font-bold text-amber-700 mb-2">
        <AlertTriangle className="w-4 h-4 animate-pulse" />
        Processing Alerts & Warnings
      </div>
      <ul className="space-y-1.5 list-disc list-inside pl-1 text-xs text-amber-900/90 font-medium">
        {warnings.map((warning, index) => (
          <li key={index} className="opacity-95">
            {warning}
          </li>
        ))}
      </ul>
    </div>
  );
}

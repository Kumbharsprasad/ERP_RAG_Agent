import React from "react";
import { Database, FileText, Cpu } from "lucide-react";

interface DataSourceBadgeProps {
  dataSource: string;
}

export default function DataSourceBadge({ dataSource }: DataSourceBadgeProps) {
  if (dataSource === "user_upload") {
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 shadow-sm">
        <FileText className="w-3.5 h-3.5" />
        Grounded in Your Files
      </span>
    );
  }

  if (dataSource === "knowledge_base" || dataSource === "rag") {
    return (
      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200 shadow-sm">
        <Database className="w-3.5 h-3.5" />
        Company Knowledge Base
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-600 border border-slate-200 shadow-sm">
      <Cpu className="w-3.5 h-3.5" />
      AI Generated
    </span>
  );
}

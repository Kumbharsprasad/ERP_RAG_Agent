import React, { useState, useRef } from "react";
import { Upload, X, File, AlertTriangle } from "lucide-react";

interface RequestFormProps {
  onSubmit: (request: string, files: File[]) => void;
  isLoading: boolean;
}

const ALLOWED_EXTENSIONS = [
  ".pdf", ".docx", ".pptx", ".xlsx", ".html", ".htm", ".csv", ".txt", ".png", ".jpg", ".jpeg"
];
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB
const MAX_FILES = 5;

export default function RequestForm({ onSubmit, isLoading }: RequestFormProps) {
  const [request, setRequest] = useState("");
  const [files, setFiles] = useState<File[]>([]);
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFiles = (newFiles: FileList | File[]): File[] => {
    setError(null);
    const valid: File[] = [];
    const currentTotal = files.length + newFiles.length;

    if (currentTotal > MAX_FILES) {
      setError(`Maximum of ${MAX_FILES} files can be uploaded.`);
      return [];
    }

    for (let i = 0; i < newFiles.length; i++) {
      const file = newFiles[i];
      const ext = "." + file.name.split(".").pop()?.toLowerCase();
      
      if (!ALLOWED_EXTENSIONS.includes(ext)) {
        setError(`File type not allowed: "${file.name}". Supported: PDF, DOCX, PPTX, XLSX, HTML, CSV, TXT, PNG, JPG`);
        return [];
      }

      if (file.size > MAX_FILE_SIZE) {
        setError(`File exceeds the 10MB size limit: "${file.name}".`);
        return [];
      }
      valid.push(file);
    }
    return valid;
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const validated = validateFiles(e.dataTransfer.files);
      if (validated.length > 0) {
        setFiles(prev => [...prev, ...validated]);
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const validated = validateFiles(e.target.files);
      if (validated.length > 0) {
        setFiles(prev => [...prev, ...validated]);
      }
    }
  };

  const removeFile = (index: number) => {
    setFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!request.trim()) {
      setError("Please write a generation request.");
      return;
    }
    onSubmit(request, files);
  };

  const loadPreset = (presetText: string) => {
    setRequest(presetText);
    setError(null);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Example Prompts Panel */}
      <div className="space-y-2.5">
        <label className="text-xs font-mono uppercase tracking-wider text-slate-500 font-semibold">
          Select Example Presets
        </label>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => loadPreset("Draft a Standard Operating Procedure (SOP) for PCCOE leave application process")}
            className="px-3.5 py-2 rounded-xl text-xs bg-slate-100/80 border border-slate-200/60 text-slate-700 hover:bg-indigo-50 hover:border-indigo-200 hover:text-indigo-600 transition-all font-medium cursor-pointer"
          >
            📝 Standard SOP
          </button>
          <button
            type="button"
            onClick={() => loadPreset("Create a casual email update about summer vacation times")}
            className="px-3.5 py-2 rounded-xl text-xs bg-slate-100/80 border border-slate-200/60 text-slate-700 hover:bg-indigo-50 hover:border-indigo-200 hover:text-indigo-600 transition-all font-medium cursor-pointer"
          >
            ❓ Ambiguous Request
          </button>
          <button
            type="button"
            onClick={() => loadPreset("Draft a business report summarizing the people strategy themes")}
            className="px-3.5 py-2 rounded-xl text-xs bg-slate-100/80 border border-slate-200/60 text-slate-700 hover:bg-indigo-50 hover:border-indigo-200 hover:text-indigo-600 transition-all font-medium cursor-pointer"
          >
            📊 File RAG Report
          </button>
        </div>
      </div>

      {/* Prompt input text area */}
      <div className="space-y-2">
        <label className="text-xs font-mono uppercase tracking-wider text-slate-500 font-semibold">
          Document Request Description
        </label>
        <textarea
          value={request}
          onChange={(e) => setRequest(e.target.value)}
          placeholder="Describe the document you want to generate (e.g., Draft an SOP for leave policies or compile a business report)..."
          disabled={isLoading}
          rows={4}
          className="w-full p-4 rounded-xl text-sm bg-slate-50 border border-slate-200 text-slate-800 placeholder-slate-400 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all resize-none custom-scrollbar shadow-inner"
        />
      </div>

      {/* Drag & Drop Upload Zone */}
      <div className="space-y-2">
        <label className="text-xs font-mono uppercase tracking-wider text-slate-500 font-semibold">
          Context Documents (Optional RAG Ingestion)
        </label>
        <div
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`flex flex-col items-center justify-center border-2 border-dashed rounded-xl p-6 transition-all cursor-pointer ${
            dragActive
              ? "border-indigo-500 bg-indigo-500/5 shadow-[0_0_15px_rgba(79,70,229,0.05)]"
              : "border-slate-300 bg-slate-50/50 hover:border-indigo-400 hover:bg-slate-100/20"
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept={ALLOWED_EXTENSIONS.join(",")}
            onChange={handleFileChange}
            className="hidden"
          />
          <Upload className="w-7 h-7 text-slate-400 mb-2.5" />
          <p className="text-xs font-semibold text-slate-700">
            Drag & drop files here, or <span className="text-indigo-600 hover:underline">browse</span>
          </p>
          <p className="text-[10px] text-slate-500 mt-1">
            PDF, DOCX, PPTX, XLSX, HTML, CSV, TXT, PNG, JPG (Max 5, 10MB each)
          </p>
        </div>

        {/* Selected files listing */}
        {files.length > 0 && (
          <div className="space-y-1.5 mt-3">
            {files.map((file, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 border border-slate-200/80 text-xs text-slate-700"
              >
                <div className="flex items-center gap-2 truncate">
                  <File className="w-4 h-4 text-indigo-600 flex-shrink-0" />
                  <span className="truncate font-medium">{file.name}</span>
                  <span className="text-[9px] text-slate-400 font-mono">
                    ({(file.size / (1024 * 1024)).toFixed(2)} MB)
                  </span>
                </div>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFile(idx);
                  }}
                  className="p-1 rounded-full hover:bg-slate-200 text-slate-500 hover:text-slate-700 transition-colors cursor-pointer"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Validation Error Message */}
      {error && (
        <div className="flex items-center gap-2 p-3 text-xs rounded-xl border border-red-200 bg-red-50/70 text-red-600 font-medium">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Submit Button */}
      <button
        type="submit"
        disabled={isLoading}
        className="w-full flex items-center justify-center px-4 py-3.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-bold text-sm rounded-xl transition-all shadow-[0_4px_12px_rgba(79,70,229,0.2)] hover:shadow-[0_6px_16px_rgba(79,70,229,0.3)] hover:scale-[1.002] active:scale-[0.998] disabled:scale-100 disabled:cursor-not-allowed cursor-pointer"
      >
        {isLoading ? "Generating Document..." : "Generate Document"}
      </button>
    </form>
  );
}

export interface SourceUsed {
  file: string;
  location: string;
  score: number;
}

export interface GenerationResponse {
  status: "success" | "partial_failure" | "rejected_non_business_query" | "error";
  document_type: string;
  plan: string[];
  facts: Record<string, any>;
  assumptions: string[];
  data_source: string;
  sources_used: SourceUsed[];
  warnings: string[];
  rejection_reason?: string;
  base64_document?: string;
  message?: string;
}

/**
 * Submits the document generation request and context files to the backend agent.
 */
export async function generateDocument(
  request: string,
  files: File[]
): Promise<GenerationResponse> {
  const apiBase = process.env.NEXT_PUBLIC_BACKEND_API_URL || "http://localhost:8000";
  const url = `${apiBase}/agent`;

  const formData = new FormData();
  formData.append("request", request);
  
  for (const file of files) {
    formData.append("files", file);
  }

  const response = await fetch(url, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    let errorDetail = "Server error occurred during generation.";
    try {
      const errorJson = await response.json();
      if (errorJson && errorJson.detail) {
        errorDetail = errorJson.detail;
      }
    } catch {
      // JSON parsing fallback
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

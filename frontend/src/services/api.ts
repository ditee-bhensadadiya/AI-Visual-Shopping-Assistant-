export interface HealthResponse {
  status: "ok";
  service: string;
  version: string;
}

export interface UploadResponse {
  id: string;
  file_type: string;
  file_size: number;
  processing_status: "uploaded" | "processing" | "completed" | "failed";
  image_url: string;
  created_at: string;
}

export interface DetectionResult {
  id: string;
  class_name: string;
  confidence: number;
  category: string | null;
  brand: string | null;
  brand_confidence: number | null;
  brand_evidence: "visible_logo" | "visible_text" | "visual_style" | "unknown" | null;
  model: string | null;
  color: string | null;
  box: { x1: number; y1: number; x2: number; y2: number };
  crop_url: string;
}

export interface DetectionRunResponse {
  upload_id: string;
  processing_status: "completed";
  image_width: number;
  image_height: number;
  analysis_provider: "ollama";
  analysis_model: string;
  detections: DetectionResult[];
}

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await fetch("/api/health", {
    method: "GET",
    headers: { Accept: "application/json" },
    signal,
  });

  if (!response.ok) {
    throw new Error(`Backend request failed (${response.status})`);
  }

  return (await response.json()) as HealthResponse;
}

export async function uploadImage(file: File, signal?: AbortSignal): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  const response = await fetch("/api/uploads", {
    method: "POST",
    headers: { Accept: "application/json" },
    body: form,
    signal,
  });

  const body = await response.json();
  if (!response.ok) {
    throw new Error(body?.error?.message ?? `Upload failed (${response.status})`);
  }
  return body as UploadResponse;
}

export async function detectUpload(uploadId: string, signal?: AbortSignal): Promise<DetectionRunResponse> {
  const response = await fetch(`/api/uploads/${encodeURIComponent(uploadId)}/detect`, {
    method: "POST",
    headers: { Accept: "application/json" },
    signal,
  });
  const body = await response.json();
  if (!response.ok) {
    throw new Error(body?.error?.message ?? `Detection failed (${response.status})`);
  }
  return body as DetectionRunResponse;
}


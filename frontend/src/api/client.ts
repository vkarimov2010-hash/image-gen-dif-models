import type {
  GenerationBatch,
  GenerationBatchSummary,
  GenerationCreateRequest,
  ModelInfo,
} from "./types";

export const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export function fetchModels(): Promise<ModelInfo[]> {
  return request<ModelInfo[]>("/models");
}

export function createGeneration(req: GenerationCreateRequest): Promise<GenerationBatch> {
  return request<GenerationBatch>("/generations", {
    method: "POST",
    body: JSON.stringify(req),
  });
}

export function fetchGeneration(id: string): Promise<GenerationBatch> {
  return request<GenerationBatch>(`/generations/${id}`);
}

export function fetchHistory(params?: {
  limit?: number;
  offset?: number;
  style?: string;
  model_id?: string;
}): Promise<GenerationBatchSummary[]> {
  const search = new URLSearchParams();
  if (params?.limit) search.set("limit", String(params.limit));
  if (params?.offset) search.set("offset", String(params.offset));
  if (params?.style) search.set("style", params.style);
  if (params?.model_id) search.set("model_id", params.model_id);
  const qs = search.toString();
  return request<GenerationBatchSummary[]>(`/generations${qs ? `?${qs}` : ""}`);
}

export function downloadUrl(batchId: string, taskId: string): string {
  return `${BASE_URL}/generations/${batchId}/tasks/${taskId}/download`;
}

export function fetchCredit(): Promise<Record<string, unknown>> {
  return request<Record<string, unknown>>("/credit");
}

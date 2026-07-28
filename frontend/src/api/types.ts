export type Style =
  | "photorealistic"
  | "anime"
  | "digital_art"
  | "3d_render"
  | "sketch"
  | "painting";

export type AspectPreset = "square" | "landscape" | "portrait" | "story" | "wide";

export interface ModelInfo {
  id: string;
  display_name: string;
  provider: string;
  supports_negative_prompt: boolean;
  supports_seed: boolean;
  estimated_credits: number;
}

export interface GenerationTask {
  id: string;
  model_id: string;
  status: "pending" | "running" | "done" | "failed" | "timeout";
  image_url: string | null;
  cost_credits: number | null;
  duration_ms: number | null;
  error: string | null;
}

export interface GenerationBatch {
  id: string;
  prompt: string;
  style: string;
  aspect_preset: string;
  purpose: string | null;
  status: "pending" | "running" | "done" | "failed";
  total_cost_credits: number;
  created_at: string;
  tasks: GenerationTask[];
}

export interface GenerationBatchSummary {
  id: string;
  prompt: string;
  style: string;
  aspect_preset: string;
  purpose: string | null;
  status: string;
  total_cost_credits: number;
  created_at: string;
  model_ids: string[];
}

export interface GenerationCreateRequest {
  prompt: string;
  style: Style;
  aspect_preset: AspectPreset;
  purpose?: string | null;
  negative_prompt?: string | null;
  seed?: number | null;
  model_ids: string[];
}

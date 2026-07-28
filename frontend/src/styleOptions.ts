import type { AspectPreset, Style } from "./api/types";

export const STYLE_OPTIONS: { id: Style; label: string }[] = [
  { id: "photorealistic", label: "Фотореализм" },
  { id: "anime", label: "Аниме" },
  { id: "digital_art", label: "Digital art" },
  { id: "3d_render", label: "3D-рендер" },
  { id: "sketch", label: "Скетч / линер" },
  { id: "painting", label: "Живопись" },
];

export const ASPECT_OPTIONS: { id: AspectPreset; label: string }[] = [
  { id: "square", label: "Квадрат (1:1)" },
  { id: "landscape", label: "Альбомная (4:3)" },
  { id: "portrait", label: "Портретная (3:4)" },
  { id: "story", label: "Сторис (9:16)" },
  { id: "wide", label: "Широкая (16:9)" },
];

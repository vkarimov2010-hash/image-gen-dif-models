import type { AspectPreset, Style } from "./api/types";

export const STYLE_OPTIONS: { id: Style; label: string }[] = [
  { id: "photorealistic", label: "Фотореализм" },
  { id: "anime", label: "Аниме" },
  { id: "digital_art", label: "Digital art" },
  { id: "3d_render", label: "3D-рендер" },
  { id: "sketch", label: "Скетч / линер" },
  { id: "painting", label: "Живопись" },
];

// Ключевые слова для эвристической проверки: похоже ли, что в промте сам
// пользователь упоминает стиль, отличный от выбранного в форме. Это только
// подсказка — наш код не понимает промт семантически, просто дописывает
// суффикс выбранного стиля в конец текста (см. _with_style_suffix в
// backend/app/registry.py), поэтому конфликтующие формулировки уходят в
// модель вместе, без разрешения противоречия на нашей стороне.
export const STYLE_CONFLICT_KEYWORDS: Record<Style, string[]> = {
  photorealistic: [
    "фотореал",
    "гиперреалист",
    "hyperrealistic",
    "photorealistic",
    "photo-realistic",
    "photoreal",
  ],
  anime: ["аниме", "манга", "anime", "manga"],
  digital_art: [
    "digital art",
    "цифровое искусство",
    "цифровая живопись",
    "концепт-арт",
    "concept art",
    "digital painting",
  ],
  "3d_render": [
    "3d render",
    "3d-рендер",
    "3д рендер",
    "octane render",
    "cgi рендер",
  ],
  sketch: [
    "скетч",
    "эскиз",
    "карандашн",
    "pencil sketch",
    "line art",
    "линарт",
  ],
  painting: [
    "живопис",
    "картина маслом",
    "oil painting",
    "акварел",
    "watercolor",
    "мазками",
  ],
};

export const ASPECT_OPTIONS: { id: AspectPreset; label: string }[] = [
  { id: "square", label: "Квадрат (1:1)" },
  { id: "landscape", label: "Альбомная (4:3)" },
  { id: "portrait", label: "Портретная (3:4)" },
  { id: "story", label: "Сторис (9:16)" },
  { id: "wide", label: "Широкая (16:9)" },
];

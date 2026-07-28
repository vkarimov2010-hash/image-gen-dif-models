import type { AspectPreset } from "./api/types";

export interface PurposePreset {
  id: string;
  label: string;
  aspectPreset: AspectPreset;
  hint: string;
}

export const PURPOSE_PRESETS: PurposePreset[] = [
  { id: "social_post", label: "Пост в соцсети", aspectPreset: "square", hint: "1:1, напр. 1080×1080" },
  { id: "telegram_avatar", label: "Аватар Telegram-канала", aspectPreset: "square", hint: "1:1, круглая обрезка" },
  { id: "telegram_cover", label: "Обложка Telegram-канала", aspectPreset: "wide", hint: "16:9" },
  { id: "instagram_story", label: "Story / Reels", aspectPreset: "story", hint: "9:16" },
  { id: "banner", label: "Баннер / обложка сайта", aspectPreset: "wide", hint: "16:9" },
  { id: "poster", label: "Постер / вертикальный принт", aspectPreset: "portrait", hint: "3:4" },
  { id: "custom", label: "Другое (выбрать вручную)", aspectPreset: "square", hint: "" },
];

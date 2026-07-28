import { useState } from "react";
import { BASE_URL, downloadUrl } from "../api/client";
import type { GenerationBatch, ModelInfo } from "../api/types";
import { ImageLightbox } from "./ImageLightbox";

interface Props {
  batch: GenerationBatch;
  models: ModelInfo[];
}

const STATUS_LABEL: Record<string, string> = {
  pending: "В очереди",
  running: "Генерируется...",
  done: "Готово",
  failed: "Ошибка",
  timeout: "Таймаут",
};

export function ResultGrid({ batch, models }: Props) {
  const modelById = new Map(models.map((m) => [m.id, m]));
  const [lightbox, setLightbox] = useState<{ src: string; alt: string } | null>(null);

  return (
    <div className="result-grid">
      {batch.tasks.map((task) => {
        const model = modelById.get(task.model_id);
        const label = model?.display_name ?? task.model_id;
        const imageSrc = task.image_url ? `${BASE_URL}${task.image_url}` : null;

        return (
          <div key={task.id} className={`result-card status-${task.status}`}>
            <div className="result-card-header">
              <strong>{label}</strong>
              <span className="status-badge">{STATUS_LABEL[task.status] ?? task.status}</span>
            </div>

            <div className="result-card-image">
              {task.status === "running" || task.status === "pending" ? (
                <div className="spinner" aria-label="Генерация..." />
              ) : task.status === "done" && imageSrc ? (
                <img
                  src={imageSrc}
                  alt={label}
                  className="result-card-image-clickable"
                  onClick={() => setLightbox({ src: imageSrc, alt: label })}
                />
              ) : (
                <div className="result-card-error">{task.error ?? "Не удалось сгенерировать"}</div>
              )}
            </div>

            <div className="result-card-footer">
              <span>{task.cost_credits != null ? `${task.cost_credits} кредитов` : "—"}</span>
              {task.status === "done" && task.image_url && (
                <a href={downloadUrl(batch.id, task.id)} download>
                  Скачать
                </a>
              )}
            </div>
          </div>
        );
      })}

      {lightbox && (
        <ImageLightbox src={lightbox.src} alt={lightbox.alt} onClose={() => setLightbox(null)} />
      )}
    </div>
  );
}

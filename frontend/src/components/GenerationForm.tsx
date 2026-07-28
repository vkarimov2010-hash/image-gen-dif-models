import { useEffect, useMemo, useState } from "react";
import type { AspectPreset, GenerationCreateRequest, ModelInfo, Style } from "../api/types";
import { PURPOSE_PRESETS } from "../purposePresets";
import { ASPECT_OPTIONS, STYLE_OPTIONS } from "../styleOptions";

interface Props {
  models: ModelInfo[];
  submitting: boolean;
  onSubmit: (req: GenerationCreateRequest) => void;
}

export function GenerationForm({ models, submitting, onSubmit }: Props) {
  const [prompt, setPrompt] = useState("");
  const [style, setStyle] = useState<Style>("photorealistic");
  const [purposeId, setPurposeId] = useState(PURPOSE_PRESETS[0].id);
  const [aspectPreset, setAspectPreset] = useState<AspectPreset>(PURPOSE_PRESETS[0].aspectPreset);
  const [aspectOverridden, setAspectOverridden] = useState(false);
  const [negativePrompt, setNegativePrompt] = useState("");
  const [seed, setSeed] = useState("");
  const [selectedModelIds, setSelectedModelIds] = useState<string[]>([]);

  useEffect(() => {
    if (models.length > 0 && selectedModelIds.length === 0) {
      setSelectedModelIds(models.map((m) => m.id));
    }
  }, [models, selectedModelIds.length]);

  const currentPurpose = useMemo(
    () => PURPOSE_PRESETS.find((p) => p.id === purposeId) ?? PURPOSE_PRESETS[0],
    [purposeId],
  );

  function handlePurposeChange(id: string) {
    setPurposeId(id);
    if (!aspectOverridden) {
      const preset = PURPOSE_PRESETS.find((p) => p.id === id);
      if (preset) setAspectPreset(preset.aspectPreset);
    }
  }

  function toggleModel(id: string) {
    setSelectedModelIds((prev) =>
      prev.includes(id) ? prev.filter((m) => m !== id) : [...prev, id],
    );
  }

  const selectedModels = models.filter((m) => selectedModelIds.includes(m.id));
  const estimatedTotal = selectedModels.reduce((sum, m) => sum + m.estimated_credits, 0);

  const canSubmit = prompt.trim().length >= 3 && selectedModelIds.length > 0 && !submitting;

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;
    onSubmit({
      prompt: prompt.trim(),
      style,
      aspect_preset: aspectPreset,
      purpose: currentPurpose.id,
      negative_prompt: negativePrompt.trim() || null,
      seed: seed.trim() ? Number(seed) : null,
      model_ids: selectedModelIds,
    });
  }

  return (
    <form className="generation-form" onSubmit={handleSubmit}>
      <label className="field">
        <span>Промт</span>
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Опишите изображение как можно детальнее..."
          rows={4}
          required
        />
      </label>

      <div className="field-row">
        <label className="field">
          <span>Стиль</span>
          <select value={style} onChange={(e) => setStyle(e.target.value as Style)}>
            {STYLE_OPTIONS.map((s) => (
              <option key={s.id} value={s.id}>
                {s.label}
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>Назначение</span>
          <select value={purposeId} onChange={(e) => handlePurposeChange(e.target.value)}>
            {PURPOSE_PRESETS.map((p) => (
              <option key={p.id} value={p.id}>
                {p.label}
              </option>
            ))}
          </select>
        </label>

        <label className="field">
          <span>Формат {currentPurpose.hint && `(${currentPurpose.hint})`}</span>
          <select
            value={aspectPreset}
            onChange={(e) => {
              setAspectPreset(e.target.value as AspectPreset);
              setAspectOverridden(true);
            }}
          >
            {ASPECT_OPTIONS.map((a) => (
              <option key={a.id} value={a.id}>
                {a.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="field-row">
        <label className="field">
          <span>Негативный промт (необязательно)</span>
          <input
            value={negativePrompt}
            onChange={(e) => setNegativePrompt(e.target.value)}
            placeholder="Чего избегать на изображении"
          />
        </label>
        <label className="field field-narrow">
          <span>Seed (необязательно)</span>
          <input value={seed} onChange={(e) => setSeed(e.target.value)} placeholder="напр. 12345" />
        </label>
      </div>

      <fieldset className="model-selector">
        <legend>Модели для сравнения</legend>
        {models.length === 0 && <p className="muted">Загрузка списка моделей...</p>}
        {models.map((m) => (
          <label key={m.id} className="model-checkbox">
            <input
              type="checkbox"
              checked={selectedModelIds.includes(m.id)}
              onChange={() => toggleModel(m.id)}
            />
            <span>
              {m.display_name} <em className="muted">({m.provider})</em>
            </span>
            <span className="muted">~{m.estimated_credits} кредитов</span>
          </label>
        ))}
      </fieldset>

      <div className="form-footer">
        <span className="estimate">
          Ориентировочная стоимость батча: <strong>~{estimatedTotal} кредитов</strong> за{" "}
          {selectedModelIds.length} {selectedModelIds.length === 1 ? "модель" : "модели"}
        </span>
        <button type="submit" disabled={!canSubmit}>
          {submitting ? "Генерируем..." : "Сгенерировать"}
        </button>
      </div>
    </form>
  );
}

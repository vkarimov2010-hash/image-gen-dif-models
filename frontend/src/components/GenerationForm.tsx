import { useEffect, useMemo, useState } from "react";
import type { AspectPreset, GenerationCreateRequest, ModelInfo, Style } from "../api/types";
import { PURPOSE_PRESETS } from "../purposePresets";
import { ASPECT_OPTIONS, STYLE_CONFLICT_KEYWORDS, STYLE_OPTIONS } from "../styleOptions";

const MAX_MODELS = 5;

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
      setSelectedModelIds(models.slice(0, MAX_MODELS).map((m) => m.id));
    }
  }, [models, selectedModelIds.length]);

  const currentPurpose = useMemo(
    () => PURPOSE_PRESETS.find((p) => p.id === purposeId) ?? PURPOSE_PRESETS[0],
    [purposeId],
  );

  const styleConflict = useMemo(() => {
    const lowerPrompt = prompt.toLowerCase();
    if (!lowerPrompt.trim()) return null;
    const conflicting = STYLE_OPTIONS.filter(
      (s) =>
        s.id !== style &&
        STYLE_CONFLICT_KEYWORDS[s.id].some((kw) => lowerPrompt.includes(kw)),
    );
    if (conflicting.length === 0) return null;
    return `В промте похоже упоминается стиль «${conflicting
      .map((s) => s.label)
      .join(
        "», «",
      )}», а в форме выбран «${STYLE_OPTIONS.find((s) => s.id === style)?.label}». Оба указания уйдут в модель вместе — результат зависит от того, что она сочтёт приоритетнее.`;
  }, [prompt, style]);

  function handlePurposeChange(id: string) {
    setPurposeId(id);
    if (!aspectOverridden) {
      const preset = PURPOSE_PRESETS.find((p) => p.id === id);
      if (preset) setAspectPreset(preset.aspectPreset);
    }
  }

  function toggleModel(id: string) {
    setSelectedModelIds((prev) => {
      if (prev.includes(id)) return prev.filter((m) => m !== id);
      if (prev.length >= MAX_MODELS) return prev;
      return [...prev, id];
    });
  }

  const selectedModels = models.filter((m) => selectedModelIds.includes(m.id));
  const estimatedTotal = selectedModels.reduce((sum, m) => sum + m.estimated_credits, 0);

  const seedSupportingModels = selectedModels.filter((m) => m.supports_seed);
  const seedHint =
    selectedModels.length === 0
      ? null
      : seedSupportingModels.length === selectedModels.length
        ? "Учитывается всеми выбранными моделями."
        : seedSupportingModels.length === 0
          ? "Ни одна из выбранных моделей не поддерживает seed — значение будет проигнорировано."
          : `Учитывается только у: ${seedSupportingModels.map((m) => m.display_name).join(", ")} (остальные ${
              selectedModels.length - seedSupportingModels.length
            } игнорируют).`;

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
        {styleConflict && <p className="field-warning">{styleConflict}</p>}
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
          {seedHint && <p className="field-hint">{seedHint}</p>}
        </label>
      </div>

      <fieldset className="model-selector">
        <legend>
          Модели для сравнения{" "}
          <span className="muted">
            (выбрано {selectedModelIds.length} из {MAX_MODELS})
          </span>
        </legend>
        {models.length === 0 && <p className="muted">Загрузка списка моделей...</p>}
        <div className="model-checkbox-list">
          {models.map((m) => {
            const checked = selectedModelIds.includes(m.id);
            const disabled = !checked && selectedModelIds.length >= MAX_MODELS;
            return (
              <label
                key={m.id}
                className={`model-checkbox${disabled ? " model-checkbox-disabled" : ""}`}
              >
                <input
                  type="checkbox"
                  checked={checked}
                  disabled={disabled}
                  onChange={() => toggleModel(m.id)}
                />
                <span>
                  {m.display_name} <em className="muted">({m.provider})</em>
                </span>
                <span className="muted">~{m.estimated_credits} кредитов</span>
              </label>
            );
          })}
        </div>
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

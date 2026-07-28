import { useEffect, useState } from "react";
import { fetchGeneration, fetchHistory, fetchModels } from "../api/client";
import type { GenerationBatch, GenerationBatchSummary, ModelInfo } from "../api/types";
import { HistoryList } from "../components/HistoryList";
import { ResultGrid } from "../components/ResultGrid";

export function HistoryPage() {
  const [batches, setBatches] = useState<GenerationBatchSummary[]>([]);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [opened, setOpened] = useState<GenerationBatch | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([fetchHistory({ limit: 50 }), fetchModels()])
      .then(([h, m]) => {
        setBatches(h);
        setModels(m);
      })
      .finally(() => setLoading(false));
  }, []);

  async function handleOpen(id: string) {
    const batch = await fetchGeneration(id);
    setOpened(batch);
  }

  return (
    <div className="history-page">
      <h2>История генераций</h2>
      {loading ? <p className="muted">Загрузка...</p> : <HistoryList batches={batches} onOpen={handleOpen} />}

      {opened && (
        <section className="results-section">
          <div className="results-section-header">
            <h3>{opened.prompt}</h3>
            <button onClick={() => setOpened(null)}>Закрыть</button>
          </div>
          <ResultGrid batch={opened} models={models} />
        </section>
      )}
    </div>
  );
}

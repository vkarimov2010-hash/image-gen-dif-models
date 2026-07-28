import { useEffect, useRef, useState } from "react";
import { createGeneration, fetchGeneration, fetchModels } from "../api/client";
import type { GenerationBatch, GenerationCreateRequest, ModelInfo } from "../api/types";
import { GenerationForm } from "../components/GenerationForm";
import { ResultGrid } from "../components/ResultGrid";

const POLL_MS = 2000;

export function GeneratePage() {
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [batch, setBatch] = useState<GenerationBatch | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<number | null>(null);

  useEffect(() => {
    fetchModels().then(setModels).catch((e) => setError(String(e)));
  }, []);

  useEffect(() => {
    return () => {
      if (pollRef.current) window.clearInterval(pollRef.current);
    };
  }, []);

  function stopPolling() {
    if (pollRef.current) {
      window.clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }

  function startPolling(id: string) {
    stopPolling();
    pollRef.current = window.setInterval(async () => {
      try {
        const updated = await fetchGeneration(id);
        setBatch(updated);
        if (updated.status === "done" || updated.status === "failed") {
          stopPolling();
        }
      } catch {
        stopPolling();
      }
    }, POLL_MS);
  }

  async function handleSubmit(req: GenerationCreateRequest) {
    setSubmitting(true);
    setError(null);
    try {
      const created = await createGeneration(req);
      setBatch(created);
      startPolling(created.id);
    } catch (e) {
      setError(String(e));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="generate-page">
      <GenerationForm models={models} submitting={submitting} onSubmit={handleSubmit} />
      {error && <p className="error-banner">{error}</p>}
      {batch && (
        <section className="results-section">
          <h2>Результаты</h2>
          <ResultGrid batch={batch} models={models} />
        </section>
      )}
    </div>
  );
}

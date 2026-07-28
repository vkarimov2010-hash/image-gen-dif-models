import type { GenerationBatchSummary } from "../api/types";

interface Props {
  batches: GenerationBatchSummary[];
  onOpen: (id: string) => void;
}

export function HistoryList({ batches, onOpen }: Props) {
  if (batches.length === 0) {
    return <p className="muted">История пуста — сгенерируйте что-нибудь на вкладке "Генерация".</p>;
  }

  return (
    <table className="history-table">
      <thead>
        <tr>
          <th>Дата</th>
          <th>Промт</th>
          <th>Стиль</th>
          <th>Модели</th>
          <th>Статус</th>
          <th>Стоимость</th>
        </tr>
      </thead>
      <tbody>
        {batches.map((b) => (
          <tr key={b.id} onClick={() => onOpen(b.id)} className="history-row">
            <td>{new Date(b.created_at).toLocaleString("ru-RU")}</td>
            <td className="history-prompt">{b.prompt}</td>
            <td>{b.style}</td>
            <td>{b.model_ids.join(", ")}</td>
            <td>{b.status}</td>
            <td>{b.total_cost_credits} кред.</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

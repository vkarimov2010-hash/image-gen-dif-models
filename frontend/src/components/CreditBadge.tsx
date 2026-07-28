import { useEffect, useState } from "react";
import { fetchCredit } from "../api/client";

export function CreditBadge() {
  const [text, setText] = useState("баланс: ...");

  useEffect(() => {
    let cancelled = false;
    fetchCredit()
      .then((data) => {
        if (cancelled) return;
        const value =
          (data as Record<string, unknown>).data ?? (data as Record<string, unknown>).credits ?? data;
        setText(`баланс: ${JSON.stringify(value)}`);
      })
      .catch(() => {
        if (!cancelled) setText("баланс недоступен");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return <span className="credit-badge">{text}</span>;
}

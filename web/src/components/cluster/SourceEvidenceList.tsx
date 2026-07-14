import { useState } from "react";
import type { ArticleSummary } from "../../client/types.gen";
import { useLang } from "../../hooks/useLang";
import { formatRelativeTime } from "../../utils/time";
import { EmptyState } from "../common";

const PAGE_SIZE = 5;

export function SourceEvidenceList({ articles }: { articles: ArticleSummary[] }) {
  const [lang] = useLang();
  const [visible, setVisible] = useState(PAGE_SIZE);

  if (articles.length === 0) return <EmptyState message="No sources recorded for this cluster." />;

  return (
    <div>
      {articles.slice(0, visible).map((a) => (
        <a
          key={a.id}
          href={a.url ?? undefined}
          target="_blank"
          rel="noreferrer"
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 70px",
            gap: 10,
            border: "1px solid var(--color-border)",
            borderRadius: "var(--radius-sm)",
            padding: "8px 11px",
            marginBottom: 6,
            textDecoration: "none",
            color: "inherit",
          }}
        >
          <div>
            <div style={{ fontSize: 11, fontWeight: 700, marginBottom: 3 }}>
              {a.source_id ?? "—"}
            </div>
            <div style={{ fontSize: 9, opacity: 0.7, fontStyle: "italic" }}>{a.title ?? ""}</div>
          </div>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: 9, opacity: 0.5 }}>{a.source_type ?? ""}</div>
            <div style={{ fontSize: 9, opacity: 0.45 }}>{formatRelativeTime(a.published_at, lang)}</div>
          </div>
        </a>
      ))}
      {visible < articles.length && (
        <button
          onClick={() => setVisible((v) => v + PAGE_SIZE)}
          style={{
            border: "1px solid var(--color-border)",
            background: "none",
            borderRadius: "var(--radius-sm)",
            padding: "7px 14px",
            fontSize: 11,
            fontWeight: 600,
            cursor: "pointer",
          }}
        >
          + Show {articles.length - visible} more sources
        </button>
      )}
    </div>
  );
}

import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { ArticleSummary, ReactionSummary } from "../../client/types.gen";
import { useLang } from "../../hooks/useLang";
import { formatRelativeTime } from "../../utils/time";
import { EmptyState } from "../common";

const PAGE_SIZE = 5;

interface EvidenceRow {
  id: string;
  label: string;
  detail: string;
  tag: string;
  publishedAt: string | null;
  url: string | null;
}

function fromArticle(a: ArticleSummary): EvidenceRow {
  return {
    id: a.id, label: a.source_id ?? "—", detail: a.title ?? "",
    tag: a.source_type ?? "", publishedAt: a.published_at ?? null, url: a.url ?? null,
  };
}

function fromReaction(r: ReactionSummary, unionTag: string): EvidenceRow {
  return {
    id: r.id, label: r.actor_name, detail: r.text ?? "",
    tag: unionTag, publishedAt: r.observed_at ?? null, url: r.url ?? null,
  };
}

export function SourceEvidenceList({
  articles, reactions = [],
}: { articles: ArticleSummary[]; reactions?: ReactionSummary[] }) {
  const { t } = useTranslation();
  const [lang] = useLang();
  const [visible, setVisible] = useState(PAGE_SIZE);

  // A union's own announcement link is a valid, citable source — not just news
  // coverage — so it belongs in this list alongside scraped articles.
  const rows: EvidenceRow[] = [
    ...articles.map(fromArticle),
    ...reactions.map((r) => fromReaction(r, t("cluster.unionAnnouncement"))),
  ];

  if (rows.length === 0) return <EmptyState message="No sources recorded for this cluster." />;

  return (
    <div>
      {rows.slice(0, visible).map((row) => (
        <a
          key={row.id}
          href={row.url ?? undefined}
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
              {row.label}
            </div>
            <div style={{ fontSize: 9, opacity: 0.7, fontStyle: "italic" }}>{row.detail}</div>
          </div>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: 9, opacity: 0.5 }}>{row.tag}</div>
            <div style={{ fontSize: 9, opacity: 0.45 }}>{formatRelativeTime(row.publishedAt, lang)}</div>
          </div>
        </a>
      ))}
      {visible < rows.length && (
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
          + Show {rows.length - visible} more sources
        </button>
      )}
    </div>
  );
}

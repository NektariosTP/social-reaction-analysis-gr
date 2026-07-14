import { useTranslation } from "react-i18next";
import type { ArticleSummary } from "../../client/types.gen";
import { EmptyState } from "../common";

export function SourceBreakdown({ articles }: { articles: ArticleSummary[] }) {
  const { t } = useTranslation();
  if (articles.length === 0) return <EmptyState />;

  const counts = new Map<string, number>();
  for (const a of articles) {
    const key = a.source_type ?? "unknown";
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  const rows = [...counts.entries()].sort((a, b) => b[1] - a[1]);
  const max = Math.max(...rows.map(([, n]) => n));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 7, fontSize: 10 }}>
      {rows.map(([type, count]) => (
        <div key={type} style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ width: 70, opacity: 0.65 }}>{type}</span>
          <span
            style={{
              height: 10,
              flex: 1,
              maxWidth: "58%",
              width: `${(count / max) * 58}%`,
              background: "var(--color-accent)",
            }}
          />
          <span>{count}</span>
        </div>
      ))}
      <div style={{ opacity: 0.4, fontSize: 9 }}>
        {t("card.sources")}: {articles.length}
      </div>
    </div>
  );
}

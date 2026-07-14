import { Link } from "react-router-dom";
import type { EventSummary } from "../../client/types.gen";
import { useLang } from "../../hooks/useLang";
import { formatRelativeTime } from "../../utils/time";
import { AxisTag, EmptyState } from "../common";

/** Backed by GET /events (already sorted last_seen DESC) — there is no
 * "most active" ranking endpoint, so this is honestly labeled "recently
 * updated" rather than claimed to be activity-ranked. */
export function TopClustersTable({ events }: { events: EventSummary[] }) {
  const [lang] = useLang();
  if (events.length === 0) return <EmptyState />;

  return (
    <div style={{ border: "1px solid var(--color-border)", borderRadius: "var(--radius-md)", fontSize: 11 }}>
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 140px 60px 70px",
          background: "var(--color-text)",
          color: "var(--color-surface)",
          fontSize: 9,
          letterSpacing: "0.07em",
          textTransform: "uppercase",
          padding: "7px 12px",
          gap: 10,
        }}
      >
        <span>Headline</span>
        <span>Axes</span>
        <span>Articles</span>
        <span>Updated</span>
      </div>
      {events.map((e, i) => (
        <Link
          key={e.id}
          to={`/cluster/${e.id}`}
          style={{
            display: "grid",
            gridTemplateColumns: "1fr 140px 60px 70px",
            padding: "9px 12px",
            gap: 10,
            alignItems: "center",
            borderTop: i === 0 ? "none" : "1px dashed var(--color-border)",
            color: "inherit",
            textDecoration: "none",
          }}
        >
          <span style={{ fontSize: 11 }}>{(lang === "el" ? e.summary_el : e.summary_en) ?? "…"}</span>
          <span style={{ display: "flex", gap: 3, flexWrap: "wrap" }}>
            {e.action_forms.slice(0, 1).map((v) => (
              <AxisTag key={v} value={v} variant="action" />
            ))}
          </span>
          <span style={{ textAlign: "center" }}>{e.article_count}</span>
          <span style={{ opacity: 0.55, fontSize: 9 }}>{formatRelativeTime(e.last_seen, lang)}</span>
        </Link>
      ))}
    </div>
  );
}

import type { DistributionItem } from "../../client/types.gen";
import { useLang } from "../../hooks/useLang";
import { axisLabel } from "../../i18n";

/** Horizontal bar breakdown for a taxonomy distribution (A1/A2/A3). Labels
 * are translated via the taxonomy dictionary when the raw value matches it;
 * otherwise (e.g. region codes) shown as-is. */
export function AxisBreakdownBar({ items, translateLabels = true }: { items: DistributionItem[]; translateLabels?: boolean }) {
  const [lang] = useLang();
  if (items.length === 0) {
    return <div style={{ fontSize: 12, color: "var(--color-text-muted)" }}>No data yet.</div>;
  }
  const max = Math.max(...items.map((d) => d.count));

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 7, fontSize: 10 }}>
      {items.map((d) => (
        <div key={d.label} style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ width: 90, opacity: 0.7, fontSize: 9, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            {translateLabels ? axisLabel(d.label, lang) : d.label}
          </span>
          <span
            style={{
              height: 11,
              width: `${(d.count / max) * 68}%`,
              background: "var(--color-accent)",
            }}
          />
          <span style={{ opacity: 0.7 }}>{d.count}</span>
        </div>
      ))}
    </div>
  );
}

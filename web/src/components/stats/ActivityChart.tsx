import type { DistributionItem } from "../../client/types.gen";
import styles from "./ActivityChart.module.css";

/** `items` must already be in chronological (oldest → newest) order. */
export function ActivityChart({ items }: { items: DistributionItem[] }) {
  if (items.length === 0) {
    return <div style={{ fontSize: 12, color: "var(--color-text-muted)" }}>No data yet.</div>;
  }
  const max = Math.max(...items.map((d) => d.count), 1);

  return (
    <div>
      <div className={styles.chart}>
        {items.map((d) => (
          <span
            key={d.label}
            className={styles.bar}
            style={{ height: `${Math.max(3, (d.count / max) * 100)}%` }}
            title={`${d.label}: ${d.count}`}
          />
        ))}
      </div>
      <div className={styles.axisLabels}>
        <span>{items[0].label}</span>
        {items.length > 2 && <span>{items[Math.floor(items.length / 2)].label}</span>}
        <span>{items[items.length - 1].label}</span>
      </div>
    </div>
  );
}

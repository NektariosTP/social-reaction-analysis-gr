import type { DistributionItem } from "../../client/types.gen";
import { EmptyState } from "../common";

export function TopLocationsTable({ items, limit = 8 }: { items: DistributionItem[]; limit?: number }) {
  if (items.length === 0) {
    return <EmptyState message="No events have a resolved region yet (geocoding hasn't assigned a periphery to any event in this dataset)." />;
  }
  const top = items.slice(0, limit);
  const rest = items.length - top.length;

  return (
    <div style={{ border: "1px solid var(--color-border)", borderRadius: "var(--radius-md)", fontSize: 11, fontWeight: 600 }}>
      {top.map((d, i) => (
        <div
          key={d.label}
          style={{
            display: "flex",
            justifyContent: "space-between",
            padding: "6px 10px",
            borderTop: i === 0 ? "none" : "1px dashed var(--color-border)",
          }}
        >
          <span>{d.label}</span>
          <span style={{ opacity: 0.6 }}>{d.count}</span>
        </div>
      ))}
      {rest > 0 && (
        <div style={{ padding: "6px 10px", borderTop: "1px dashed var(--color-border)", opacity: 0.5, fontSize: 10 }}>
          + {rest} more
        </div>
      )}
    </div>
  );
}

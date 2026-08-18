import type { EventSummary } from "../../client/types.gen";
import { AxisBreakdownBar } from "../stats/AxisBreakdownBar";
import styles from "./AreaBlock.module.css";

export interface AreaBlockProps {
  title: string;
  events: EventSummary[];
  loading: boolean;
  onClose: () => void;
}

function distribution(events: EventSummary[], key: (e: EventSummary) => string | null | undefined) {
  const counts = new Map<string, number>();
  for (const e of events) {
    const v = key(e);
    if (v) counts.set(v, (counts.get(v) ?? 0) + 1);
  }
  return [...counts.entries()].map(([label, count]) => ({ label, count }));
}

export function AreaBlock({ title, events, loading, onClose }: AreaBlockProps) {
  const byIntensity = distribution(events, (e) => e.intensity);
  const byThematic = distribution(events, (e) => e.thematic_fields[0]);

  return (
    <div className={styles.block}>
      <div className={styles.header}>
        <span>{title}</span>
        <button type="button" aria-label="Close area view" onClick={onClose}>×</button>
      </div>
      {loading ? (
        <p className={styles.empty}>…</p>
      ) : events.length === 0 ? (
        <p className={styles.empty}>No events in this area yet.</p>
      ) : (
        <>
          <div className={styles.count}>{events.length} events</div>
          <div className={styles.charts}>
            <AxisBreakdownBar items={byIntensity} />
            <AxisBreakdownBar items={byThematic} />
          </div>
          <p className={styles.note}>Municipality coverage is best-effort; some events show only at the periphery level.</p>
        </>
      )}
    </div>
  );
}

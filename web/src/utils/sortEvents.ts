import type { EventSummary } from "../client/types.gen";

/** Group A = scheduled for today or the future; Group B = everything else. */
function group(e: EventSummary): 0 | 1 {
  return e.temporal_status === "today" || e.temporal_status === "upcoming" ? 0 : 1;
}

/** Calendar-day key ("YYYY-MM-DD") for same-day tiebreak comparisons. */
function dayKey(iso?: string | null): string {
  return iso ? new Date(iso).toISOString().slice(0, 10) : "";
}

/**
 * Feed order: today/upcoming events first (soonest event_time at the top),
 * then everything else by recency. Same-day ties go to the event with more
 * articles. Returns a new array; never mutates the input.
 */
export function sortEventsForFeed(events: EventSummary[]): EventSummary[] {
  return [...events].sort((a, b) => {
    const ga = group(a);
    const gb = group(b);
    if (ga !== gb) return ga - gb; // group A (0) before group B (1)

    const ca = a.article_count ?? 0;
    const cb = b.article_count ?? 0;

    if (ga === 0) {
      const da = dayKey(a.event_time);
      const db = dayKey(b.event_time);
      if (da !== db) return da < db ? -1 : 1; // ascending: soonest day first
      if (ca !== cb) return cb - ca; // more articles first
      return (a.event_time ?? "") < (b.event_time ?? "") ? -1 : 1;
    }

    const da = dayKey(a.last_seen);
    const db = dayKey(b.last_seen);
    if (da !== db) return da > db ? -1 : 1; // descending: most recent day first
    if (ca !== cb) return cb - ca;
    return (a.last_seen ?? "") > (b.last_seen ?? "") ? -1 : 1;
  });
}

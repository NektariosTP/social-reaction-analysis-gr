import { useCallback, useMemo } from "react";
import { useSearchParams } from "react-router-dom";

export type TimeRange = "24h" | "7d" | "30d" | "all";

export interface FilterState {
  actionForms: string[];
  thematicFields: string[];
  channel: string | null;
  intensities: string[];
  timeRange: TimeRange;
}

const TIME_RANGE_HOURS: Record<TimeRange, number | null> = {
  "24h": 24,
  "7d": 24 * 7,
  "30d": 24 * 30,
  all: null,
};

export function timeRangeToDateFrom(range: TimeRange): string | undefined {
  const hours = TIME_RANGE_HOURS[range];
  if (hours === null) return undefined;
  return new Date(Date.now() - hours * 60 * 60 * 1000).toISOString();
}

// Taxonomy values may contain literal commas (e.g. the Intensity "Disruptive"
// label), so list items are percent-encoded before joining/splitting on ",".
function parseList(params: URLSearchParams, key: string): string[] {
  const raw = params.get(key);
  return raw ? raw.split(",").filter(Boolean).map(decodeURIComponent) : [];
}

function serializeList(values: string[]): string {
  return values.map(encodeURIComponent).join(",");
}

// A real empty array already means "all selected" (see below), so "every value
// explicitly deselected" needs its own marker to stay distinguishable. Never a
// real taxonomy value.
const NONE_SENTINEL = "__none__";

/**
 * Resolves a checkbox toggle against an "empty selection means all selected" sentinel.
 * The opposite extreme — nothing selected — is represented as `[NONE_SENTINEL]` so it
 * doesn't collide with the "all" sentinel (`[]`); `set.has()`/`includes()` checks against
 * real taxonomy values naturally treat that marker as a non-match, so callers filtering
 * on the resolved list don't need to special-case it.
 */
export function toggleWithAllSentinel(all: string[], selected: string[], value: string): string[] {
  const isNone = selected.length === 1 && selected[0] === NONE_SENTINEL;
  const base = selected.length === 0 ? all : isNone ? [] : selected;
  const next = base.includes(value) ? base.filter((v) => v !== value) : [...base, value];
  if (next.length === all.length) return [];
  if (next.length === 0) return [NONE_SENTINEL];
  return next;
}

/** Keeps filter selections in the URL so views are shareable/bookmarkable. */
export function useFilterState() {
  const [params, setParams] = useSearchParams();

  const filters: FilterState = useMemo(
    () => ({
      actionForms: parseList(params, "a1"),
      thematicFields: parseList(params, "a2"),
      channel: params.get("a3"),
      intensities: parseList(params, "a4"),
      timeRange: (params.get("t") as TimeRange | null) ?? "all",
    }),
    [params],
  );

  const setFilters = useCallback(
    (next: Partial<FilterState>) => {
      setParams(
        (prev) => {
          const merged = { ...filters, ...next };
          const out = new URLSearchParams(prev);

          if (merged.actionForms.length) out.set("a1", serializeList(merged.actionForms));
          else out.delete("a1");

          if (merged.thematicFields.length) out.set("a2", serializeList(merged.thematicFields));
          else out.delete("a2");

          if (merged.channel) out.set("a3", merged.channel);
          else out.delete("a3");

          if (merged.intensities.length) out.set("a4", serializeList(merged.intensities));
          else out.delete("a4");

          if (merged.timeRange !== "all") out.set("t", merged.timeRange);
          else out.delete("t");

          return out;
        },
        { replace: true },
      );
    },
    [filters, setParams],
  );

  const toggleInList = useCallback(
    (key: "actionForms" | "thematicFields" | "intensities", value: string) => {
      const current = filters[key];
      const next = current.includes(value)
        ? current.filter((v) => v !== value)
        : [...current, value];
      setFilters({ [key]: next });
    },
    [filters, setFilters],
  );

  return { filters, setFilters, toggleInList };
}

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

function parseList(params: URLSearchParams, key: string): string[] {
  const raw = params.get(key);
  return raw ? raw.split(",").filter(Boolean) : [];
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

          if (merged.actionForms.length) out.set("a1", merged.actionForms.join(","));
          else out.delete("a1");

          if (merged.thematicFields.length) out.set("a2", merged.thematicFields.join(","));
          else out.delete("a2");

          if (merged.channel) out.set("a3", merged.channel);
          else out.delete("a3");

          if (merged.intensities.length) out.set("a4", merged.intensities.join(","));
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

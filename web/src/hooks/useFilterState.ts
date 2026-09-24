import { useCallback, useMemo } from "react";
import { useSearchParams } from "react-router-dom";

export interface FilterState {
  actionForms: string[];
  thematicFields: string[];
  channel: string | null;
  /** Single-select, like channel: exact intensity value or null for "All". */
  intensity: string | null;
  /** ISO YYYY-MM-DD local day to time-travel to, or null for Live (present). */
  day: string | null;
  /** Preset range window in days (7/15/30), past-only, or null. Mutually
   * exclusive with `day`. */
  windowDays: number | null;
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

/** Keeps filter selections in the URL so views are shareable/bookmarkable. */
export function useFilterState() {
  const [params, setParams] = useSearchParams();

  const filters: FilterState = useMemo(
    () => ({
      actionForms: parseList(params, "a1"),
      thematicFields: parseList(params, "a2"),
      channel: params.get("a3"),
      intensity: params.get("a4"),
      day: params.get("d"),
      windowDays: params.get("w") ? Number(params.get("w")) : null,
    }),
    [params],
  );

  const setFilters = useCallback(
    (next: Partial<FilterState>) => {
      setParams(
        (prev) => {
          const merged = { ...filters, ...next };
          // Range is single-mode: a preset window and an exact day cannot both
          // be active. The most recent choice wins.
          if (next.windowDays != null) merged.day = null;
          if (next.day != null) merged.windowDays = null;
          const out = new URLSearchParams(prev);

          if (merged.actionForms.length) out.set("a1", serializeList(merged.actionForms));
          else out.delete("a1");

          if (merged.thematicFields.length) out.set("a2", serializeList(merged.thematicFields));
          else out.delete("a2");

          if (merged.channel) out.set("a3", merged.channel);
          else out.delete("a3");

          if (merged.intensity) out.set("a4", merged.intensity);
          else out.delete("a4");

          if (merged.day) out.set("d", merged.day);
          else out.delete("d");

          if (merged.windowDays != null) out.set("w", String(merged.windowDays));
          else out.delete("w");

          return out;
        },
        { replace: true },
      );
    },
    [filters, setParams],
  );

  const toggleInList = useCallback(
    (key: "actionForms" | "thematicFields", value: string) => {
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

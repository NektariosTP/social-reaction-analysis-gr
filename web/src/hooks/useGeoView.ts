import { useCallback, useMemo } from "react";
import { useSearchParams } from "react-router-dom";

export type GeoLevel = "none" | "periphery" | "municipality";

export interface GeoView {
  level: GeoLevel;
  region: string | null;
  municipality: string | null;
}

/** URL-backed periphery/municipality drill-down state. `muni` without `region` is ignored. */
export function useGeoView() {
  const [params, setParams] = useSearchParams();

  const view: GeoView = useMemo(() => {
    const region = params.get("region");
    const muni = params.get("muni");
    if (region && muni) return { level: "municipality", region, municipality: muni };
    if (region) return { level: "periphery", region, municipality: null };
    return { level: "none", region: null, municipality: null };
  }, [params]);

  const write = useCallback(
    (mut: (out: URLSearchParams) => void) => {
      setParams(
        (prev) => {
          const out = new URLSearchParams(prev);
          mut(out);
          return out;
        },
        { replace: true },
      );
    },
    [setParams],
  );

  const selectPeriphery = useCallback(
    (name: string) => write((out) => { out.set("region", name); out.delete("muni"); }),
    [write],
  );
  const selectMunicipality = useCallback(
    (name: string) => {
      if (!params.get("region")) return; // no-op without a periphery
      write((out) => out.set("muni", name));
    },
    [write, params],
  );
  const clearMunicipality = useCallback(() => write((out) => out.delete("muni")), [write]);
  const clear = useCallback(
    () => write((out) => { out.delete("region"); out.delete("muni"); }),
    [write],
  );

  return { ...view, selectPeriphery, selectMunicipality, clearMunicipality, clear };
}

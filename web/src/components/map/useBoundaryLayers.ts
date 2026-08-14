import { useEffect } from "react";
import type maplibregl from "maplibre-gl";
import { usePeripheryBoundaries, useMunicipalityBoundaries } from "../../api/queries";
import type { GeoView } from "../../hooks/useGeoView";

interface BoundaryHandlers {
  selectPeriphery(name: string): void;
  selectMunicipality(name: string): void;
}

const PERIPHERY_SRC = "peripheries";
const MUNI_SRC = "municipalities";

function ensureSource(map: maplibregl.Map, id: string, data: unknown) {
  const existing = map.getSource(id) as { setData?: (d: unknown) => void } | undefined;
  if (existing?.setData) existing.setData(data);
  else map.addSource(id, { type: "geojson", data, generateId: true } as never);
}

/** Adds periphery + municipality GL layers driven by the geo view. Marker effect is untouched. */
export function useBoundaryLayers(
  map: maplibregl.Map | null,
  view: Pick<GeoView, "level" | "region" | "municipality">,
  handlers: BoundaryHandlers,
) {
  const peripheries = usePeripheryBoundaries();
  const municipalities = useMunicipalityBoundaries(view.region);

  // Periphery fill + line, always present once data + map are ready.
  useEffect(() => {
    if (!map || !peripheries.data) return;
    ensureSource(map, PERIPHERY_SRC, peripheries.data);
    if (!map.getLayer("peripheries-fill")) {
      map.addLayer({ id: "peripheries-fill", type: "fill", source: PERIPHERY_SRC, paint: { "fill-color": "#4f7cac", "fill-opacity": 0.08 } } as never);
      map.addLayer({ id: "peripheries-line", type: "line", source: PERIPHERY_SRC, paint: { "line-color": "#4f7cac", "line-width": 1 } } as never);
    }
    const onClick = (e: maplibregl.MapLayerMouseEvent) => {
      const name = e.features?.[0]?.properties?.name as string | undefined;
      if (name) handlers.selectPeriphery(name);
    };
    map.on("click", "peripheries-fill", onClick);
    return () => { map.off("click", "peripheries-fill", onClick); };
  }, [map, peripheries.data, handlers]);

  // Municipality fill + line, only while a periphery is selected.
  useEffect(() => {
    if (!map) return;
    if (view.level === "none" || !municipalities.data) {
      ["municipalities-fill", "municipalities-line"].forEach((id) => { if (map.getLayer(id)) map.removeLayer(id); });
      if (map.getSource(MUNI_SRC)) map.removeSource(MUNI_SRC);
      return;
    }
    ensureSource(map, MUNI_SRC, municipalities.data);
    if (!map.getLayer("municipalities-fill")) {
      map.addLayer({ id: "municipalities-fill", type: "fill", source: MUNI_SRC, paint: { "fill-color": "#e08a3c", "fill-opacity": 0.12 } } as never);
      map.addLayer({ id: "municipalities-line", type: "line", source: MUNI_SRC, paint: { "line-color": "#e08a3c", "line-width": 1 } } as never);
    }
    const onClick = (e: maplibregl.MapLayerMouseEvent) => {
      const name = e.features?.[0]?.properties?.name as string | undefined;
      if (name) handlers.selectMunicipality(name);
    };
    map.on("click", "municipalities-fill", onClick);
    return () => { map.off("click", "municipalities-fill", onClick); };
  }, [map, view.level, municipalities.data, handlers]);
}

import { useEffect } from "react";
import type maplibregl from "maplibre-gl";
import { LngLatBounds } from "maplibre-gl";
import { usePeripheryBoundaries, useMunicipalityBoundaries } from "../../api/queries";
import type { GeoView } from "../../hooks/useGeoView";

interface BoundaryHandlers {
  selectPeriphery(name: string): void;
  selectMunicipality(name: string): void;
}

interface NamedBoundaryFeature {
  geometry: { coordinates?: unknown };
  properties: { name: string };
}

const PERIPHERY_SRC = "peripheries";
const MUNI_SRC = "municipalities";

function ensureSource(map: maplibregl.Map, id: string, data: unknown) {
  const existing = map.getSource(id) as { setData?: (d: unknown) => void } | undefined;
  if (existing?.setData) existing.setData(data);
  else map.addSource(id, { type: "geojson", data, generateId: true } as never);
}

function extendBounds(bounds: LngLatBounds, coords: unknown): void {
  if (!Array.isArray(coords)) return;
  if (typeof coords[0] === "number") bounds.extend(coords as [number, number]);
  else for (const c of coords) extendBounds(bounds, c);
}

function fitToFeature(
  map: maplibregl.Map,
  feature: NamedBoundaryFeature | undefined,
  padding: number,
  maxZoom: number,
  obstructedLeft: number,
) {
  if (!feature?.geometry.coordinates) return;
  const bounds = new LngLatBounds();
  extendBounds(bounds, feature.geometry.coordinates);
  // The floating sidebar overlays the left edge of the map — pad that side extra so
  // fitted content isn't centered underneath it (e.g. a selected municipality's western
  // exclaves rendering invisibly behind the panel).
  map.fitBounds(bounds, {
    padding: { top: padding, bottom: padding, right: padding, left: padding + obstructedLeft },
    maxZoom,
    duration: 800,
  } as never);
}

/** Adds periphery + municipality GL layers driven by the geo view. Marker effect is untouched. */
export function useBoundaryLayers(
  map: maplibregl.Map | null,
  view: Pick<GeoView, "level" | "region" | "municipality">,
  handlers: BoundaryHandlers,
  obstructedLeft = 0,
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
    // Once a specific municipality is picked, render only that one — the periphery can
    // hold dozens of them (South Aegean has 34), and drawing every neighboring island's
    // outline on top of the selected one is visual noise, not detail.
    const data =
      view.level === "municipality"
        ? { ...municipalities.data, features: municipalities.data.features.filter((f) => f.properties.name === view.municipality) }
        : municipalities.data;
    ensureSource(map, MUNI_SRC, data);
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
  }, [map, view.level, view.municipality, municipalities.data, handlers]);

  // Hide the periphery fill/outline once its municipalities are on screen — at that point
  // the country-wide shape is just clutter under the municipality layer. The AreaBlock
  // column keeps showing the periphery name regardless.
  useEffect(() => {
    if (!map) return;
    const visibility = view.level === "none" ? "visible" : "none";
    if (map.getLayer("peripheries-fill")) map.setLayoutProperty("peripheries-fill", "visibility", visibility);
    if (map.getLayer("peripheries-line")) map.setLayoutProperty("peripheries-line", "visibility", visibility);
  }, [map, view.level, peripheries.data]);

  // Zoom to the selected periphery.
  useEffect(() => {
    if (!map || !view.region) return;
    const feature = peripheries.data?.features.find((f) => f.properties.name === view.region);
    fitToFeature(map, feature, 40, 10, obstructedLeft);
  }, [map, view.region, peripheries.data, obstructedLeft]);

  // Zoom to the selected municipality (tighter padding — much smaller area).
  useEffect(() => {
    if (!map || !view.municipality) return;
    const feature = municipalities.data?.features.find((f) => f.properties.name === view.municipality);
    fitToFeature(map, feature, 60, 13, obstructedLeft);
  }, [map, view.municipality, municipalities.data, obstructedLeft]);
}

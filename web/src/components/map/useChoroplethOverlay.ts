import { useEffect } from "react";
import type maplibregl from "maplibre-gl";
import type { ChoroplethValue } from "../../client/types.gen";
import { useChoropleth, usePeripheryBoundaries } from "../../api/queries";

const NO_DATA = "#cccccc";
const RAMP = ["#f7fbff", "#c6dbef", "#6baed6", "#2171b5", "#08306b"];

type ChoroplethExpression = string | unknown[];

/** Blend two "#rrggbb" colors; t in [0,1]. */
function lerpColor(a: string, b: string, t: number): string {
  const pa = [1, 3, 5].map((i) => parseInt(a.slice(i, i + 2), 16));
  const pb = [1, 3, 5].map((i) => parseInt(b.slice(i, i + 2), 16));
  const ch = pa.map((v, i) => Math.round(v + (pb[i] - v) * t));
  return "#" + ch.map((v) => v.toString(16).padStart(2, "0")).join("");
}

/** Sequential ramp color at fraction f in [0,1]. */
function rampColor(f: number): string {
  const p = Math.max(0, Math.min(1, f)) * (RAMP.length - 1);
  const lo = Math.floor(p);
  if (lo >= RAMP.length - 1) return RAMP[RAMP.length - 1];
  return lerpColor(RAMP[lo], RAMP[lo + 1], p - lo);
}

/** value → rank fraction in [0,1] over the distinct present values (ties share a rank). */
function rankFractions(values: ChoroplethValue[]): Map<number, number> {
  const distinct = [...new Set(values.filter((v) => v.value != null).map((v) => v.value as number))].sort(
    (x, y) => x - y,
  );
  const out = new Map<number, number>();
  distinct.forEach((v, i) => out.set(v, distinct.length === 1 ? 0.5 : i / (distinct.length - 1)));
  return out;
}

export function buildChoroplethExpression(values: ChoroplethValue[]): ChoroplethExpression {
  const ranks = rankFractions(values);
  if (ranks.size === 0) return NO_DATA;
  const expr: unknown[] = ["match", ["get", "region_code"]];
  for (const v of values) {
    if (v.value == null) continue;
    expr.push(v.region_code, rampColor(ranks.get(v.value as number) ?? 0.5));
  }
  expr.push(NO_DATA);
  return expr as ChoroplethExpression;
}

export function formatChoroplethValue(value: number, unit?: string | null): string {
  const num = new Intl.NumberFormat("en-US", { maximumFractionDigits: 1 }).format(value);
  return unit === "%" ? `${num}%` : num;
}

export function buildLabelExpression(values: ChoroplethValue[]): ChoroplethExpression {
  const present = values.filter((v) => v.value != null);
  if (present.length === 0) return "";
  const expr: unknown[] = ["match", ["get", "region_code"]];
  for (const v of present) {
    expr.push(v.region_code, formatChoroplethValue(v.value as number, v.unit));
  }
  expr.push("");
  return expr as ChoroplethExpression;
}

type Ring = [number, number][];

interface LabelBoundaryFeature {
  geometry: { type?: unknown; coordinates?: unknown };
  properties?: { region_code?: string | null } | null;
}
interface LabelBoundaryCollection {
  features: LabelBoundaryFeature[];
}

/** Outer ring of each polygon part — Polygon has one, MultiPolygon has one per part. */
function outerRings(geometry: { type?: unknown; coordinates?: unknown }): Ring[] {
  if (geometry.type === "Polygon") {
    const coords = geometry.coordinates as Ring[] | undefined;
    return coords?.[0] ? [coords[0]] : [];
  }
  if (geometry.type === "MultiPolygon") {
    const coords = (geometry.coordinates as Ring[][] | undefined) ?? [];
    return coords.map((poly) => poly[0]).filter((ring): ring is Ring => !!ring);
  }
  return [];
}

/** Shoelace-formula signed area of a closed ring (positive/negative by winding). */
function ringArea(ring: Ring): number {
  let a = 0;
  for (let i = 0; i < ring.length - 1; i++) {
    const [x0, y0] = ring[i];
    const [x1, y1] = ring[i + 1];
    a += x0 * y1 - x1 * y0;
  }
  return a / 2;
}

/** True area centroid of a closed ring (not a naive vertex average, which skews toward denser coastline). */
function ringCentroid(ring: Ring): [number, number] {
  let a = 0, cx = 0, cy = 0;
  for (let i = 0; i < ring.length - 1; i++) {
    const [x0, y0] = ring[i];
    const [x1, y1] = ring[i + 1];
    const cross = x0 * y1 - x1 * y0;
    a += cross;
    cx += (x0 + x1) * cross;
    cy += (y0 + y1) * cross;
  }
  a /= 2;
  if (a === 0) {
    const n = ring.length || 1;
    return [ring.reduce((s, p) => s + p[0], 0) / n, ring.reduce((s, p) => s + p[1], 0) / n];
  }
  return [cx / (6 * a), cy / (6 * a)];
}

/**
 * One Point feature per periphery that has a value, anchored at the centroid
 * of its largest polygon part. Peripheries with disjoint island chains (South
 * Aegean, Ionian Islands, Attica, ...) are MultiPolygons; a symbol layer with
 * symbol-placement:"point" sourced directly from that polygon data places one
 * label per constituent polygon (i.e. per island), not per feature — and a
 * separately hand-maintained coordinate list drifts out of sync with the real
 * region_code values (e.g. "West Macedonia" vs "Western Macedonia") and isn't
 * precise enough to land inside the actual shape. Computing the anchor from
 * the same boundary geometry that backs the fill layer avoids both problems.
 */
export function buildLabelPoints(
  values: ChoroplethValue[],
  boundaries: LabelBoundaryCollection,
): GeoJSON.FeatureCollection {
  const present = new Set(values.filter((v) => v.value != null).map((v) => v.region_code));
  const features: GeoJSON.Feature[] = [];
  for (const f of boundaries.features) {
    const code = f.properties?.region_code;
    if (!code || !present.has(code)) continue;
    const rings = outerRings(f.geometry);
    if (rings.length === 0) continue;
    const largest = rings.reduce((best, r) => (Math.abs(ringArea(r)) > Math.abs(ringArea(best)) ? r : best));
    features.push({
      type: "Feature",
      geometry: { type: "Point", coordinates: ringCentroid(largest) },
      properties: { region_code: code },
    });
  }
  return { type: "FeatureCollection", features };
}

const SRC = "choropleth-src";
const LABEL_SRC = "choropleth-label-src";
const LAYER = "choropleth-fill";
const LABEL_LAYER = "choropleth-label";
const EMPTY_POINTS: GeoJSON.FeatureCollection = { type: "FeatureCollection", features: [] };

/** Data-driven fill + value labels shading periphery boundaries by the selected indicator. */
export function useChoroplethOverlay(
  map: maplibregl.Map | null,
  styleLoaded: boolean,
  indicator: string | null,
) {
  const { data: values } = useChoropleth(indicator);
  const { data: boundaries } = usePeripheryBoundaries();

  useEffect(() => {
    if (!map || !styleLoaded || !boundaries) return;
    if (!indicator) {
      if (map.getLayer(LABEL_LAYER)) map.removeLayer(LABEL_LAYER);
      if (map.getLayer(LAYER)) map.removeLayer(LAYER);
      if (map.getSource(SRC)) map.removeSource(SRC);
      if (map.getSource(LABEL_SRC)) map.removeSource(LABEL_SRC);
      return;
    }
    if (!map.getSource(SRC)) {
      map.addSource(SRC, { type: "geojson", data: boundaries } as never);
      map.addLayer({
        id: LAYER, type: "fill", source: SRC,
        paint: { "fill-opacity": 0.55, "fill-color": NO_DATA },
      } as never);
    }
    if (!map.getSource(LABEL_SRC)) {
      map.addSource(LABEL_SRC, { type: "geojson", data: EMPTY_POINTS } as never);
      map.addLayer({
        id: LABEL_LAYER, type: "symbol", source: LABEL_SRC,
        layout: {
          "text-field": "",
          "text-size": 13,
          "text-font": ["Open Sans Bold", "Arial Unicode MS Bold"],
        },
        paint: {
          "text-color": "#111111",
          "text-halo-color": "#ffffff",
          "text-halo-width": 1.5,
        },
      } as never);
    }
    const rows = values?.values ?? [];
    map.setPaintProperty(LAYER, "fill-color", buildChoroplethExpression(rows) as never);
    (map.getSource(LABEL_SRC) as maplibregl.GeoJSONSource).setData(
      buildLabelPoints(rows, boundaries) as never,
    );
    map.setLayoutProperty(LABEL_LAYER, "text-field", buildLabelExpression(rows) as never);
  }, [map, styleLoaded, boundaries, indicator, values]);
}

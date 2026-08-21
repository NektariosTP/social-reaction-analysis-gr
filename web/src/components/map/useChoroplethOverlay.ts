import { useEffect } from "react";
import type maplibregl from "maplibre-gl";
import type { ChoroplethValue } from "../../client/types.gen";
import { useChoropleth, usePeripheryBoundaries } from "../../api/queries";

const NO_DATA = "#cccccc";
const RAMP = ["#f7fbff", "#c6dbef", "#6baed6", "#2171b5", "#08306b"];

type ChoroplethExpression = string | unknown[];

function color(value: number, min: number, max: number): string {
  if (max <= min) return RAMP[2];
  const idx = Math.min(RAMP.length - 1, Math.floor(((value - min) / (max - min)) * RAMP.length));
  return RAMP[idx];
}

export function buildChoroplethExpression(values: ChoroplethValue[]): ChoroplethExpression {
  const nums = values.filter((v) => v.value != null).map((v) => v.value as number);
  if (nums.length === 0) return NO_DATA;
  const min = Math.min(...nums);
  const max = Math.max(...nums);
  const expr: unknown[] = ["match", ["get", "region_code"]];
  for (const v of values) {
    if (v.value == null) continue;
    expr.push(v.region_code, color(v.value, min, max));
  }
  expr.push(NO_DATA);
  return expr as ChoroplethExpression;
}

const SRC = "choropleth-src";
const LAYER = "choropleth-fill";

/** Data-driven fill layer shading periphery boundaries by the selected indicator's latest value. */
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
      if (map.getLayer(LAYER)) map.removeLayer(LAYER);
      if (map.getSource(SRC)) map.removeSource(SRC);
      return;
    }
    if (!map.getSource(SRC)) {
      map.addSource(SRC, { type: "geojson", data: boundaries } as never);
      map.addLayer({
        id: LAYER, type: "fill", source: SRC,
        paint: { "fill-opacity": 0.45, "fill-color": NO_DATA },
      } as never);
    }
    const expr = buildChoroplethExpression(values?.values ?? []);
    map.setPaintProperty(LAYER, "fill-color", expr as never);
  }, [map, styleLoaded, boundaries, indicator, values]);
}

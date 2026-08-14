import { describe, expect, it, vi, beforeEach } from "vitest";
vi.mock("maplibre-gl");
vi.mock("../../api/queries", () => ({
  usePeripheryBoundaries: () => ({
    data: { type: "FeatureCollection", features: [{ type: "Feature", geometry: { type: "Polygon", coordinates: [[[23.7, 38], [23.8, 38], [23.8, 38.1], [23.7, 38]]] }, properties: { name: "Attica", region_code: "Attica" } }] },
  }),
  useMunicipalityBoundaries: (region: string | null) => ({
    data: region
      ? { type: "FeatureCollection", features: [{ type: "Feature", geometry: { type: "Polygon", coordinates: [[[23.7, 38], [23.75, 38], [23.75, 38.05], [23.7, 38]]] }, properties: { name: "Δήμος Αθηναίων", region_code: "Attica" } }] }
      : undefined,
  }),
}));

import maplibregl from "maplibre-gl";
import { renderHook } from "@testing-library/react";
import { useBoundaryLayers } from "./useBoundaryLayers";

const mock = maplibregl as unknown as {
  Map: new (o: Record<string, unknown>) => maplibregl.Map;
  mapSourceCalls: { id: string }[];
  mapLayerCalls: { layer: { id: string } }[];
};

beforeEach(() => {
  mock.mapSourceCalls.length = 0;
  mock.mapLayerCalls.length = 0;
});

describe("useBoundaryLayers", () => {
  it("adds a peripheries source and fill/line layers", () => {
    const map = new mock.Map({});
    renderHook(() =>
      useBoundaryLayers(map, { level: "none", region: null, municipality: null }, { selectPeriphery: vi.fn(), selectMunicipality: vi.fn() }),
    );
    expect(mock.mapSourceCalls.some((s) => s.id === "peripheries")).toBe(true);
    const layerIds = mock.mapLayerCalls.map((l) => l.layer.id);
    expect(layerIds).toEqual(expect.arrayContaining(["peripheries-fill", "peripheries-line"]));
  });

  it("adds a municipalities source when a region is selected", () => {
    const map = new mock.Map({});
    renderHook(() =>
      useBoundaryLayers(map, { level: "periphery", region: "Attica", municipality: null }, { selectPeriphery: vi.fn(), selectMunicipality: vi.fn() }),
    );
    expect(mock.mapSourceCalls.some((s) => s.id === "municipalities")).toBe(true);
  });
});

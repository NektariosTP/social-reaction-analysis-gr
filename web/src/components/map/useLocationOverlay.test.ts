import { describe, expect, it, vi, beforeEach } from "vitest";
vi.mock("maplibre-gl");
import maplibregl from "maplibre-gl";
import { renderHook } from "@testing-library/react";
import type { GeoJsonFeature } from "../../client/types.gen";
import { useLocationOverlay } from "./useLocationOverlay";

const mock = maplibregl as unknown as {
  Map: new (o: Record<string, unknown>) => maplibregl.Map;
  mapSourceCalls: { id: string }[];
  mapLayerCalls: { layer: { id: string } }[];
  mapSetDataCalls: { id: string; data: unknown }[];
};

beforeEach(() => {
  mock.mapSourceCalls.length = 0;
  mock.mapLayerCalls.length = 0;
  mock.mapSetDataCalls.length = 0;
});

function multiLocFeature(id: string): GeoJsonFeature {
  return {
    type: "Feature",
    geometry: { type: "Point", coordinates: [23.7, 38.0] },
    properties: {
      id,
      action_forms: [],
      thematic_fields: [],
      channel: null,
      intensity: "Ειρηνική",
      summary_en: null,
      article_count: 1,
      first_seen: null,
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      locations: [
        { lat: 38.0, lon: 23.7, is_primary: true },
        { lat: 40.6, lon: 22.9, is_primary: false },
      ] as any,
    },
  } as GeoJsonFeature;
}

describe("useLocationOverlay", () => {
  it("adds the overlay sources and both layers when style is loaded", () => {
    const map = new mock.Map({});
    renderHook(() => useLocationOverlay(map, true, vi.fn()));
    const layerIds = mock.mapLayerCalls.map((l) => l.layer.id);
    expect(layerIds).toEqual(expect.arrayContaining(["event-connectors", "event-secondaries"]));
  });

  it("pushes derived data to the sources on updateOverlay", () => {
    const map = new mock.Map({});
    const { result } = renderHook(() => useLocationOverlay(map, true, vi.fn()));
    result.current.updateOverlay([multiLocFeature("a")], "a");
    // one secondary + one connector collection pushed
    expect(mock.mapSetDataCalls.length).toBeGreaterThanOrEqual(2);
    const pushed = mock.mapSetDataCalls.map((c) => c.data as GeoJSON.FeatureCollection);
    expect(pushed.some((fc) => fc.features.length === 1)).toBe(true);
  });

  it("does nothing before the style is loaded", () => {
    const map = new mock.Map({});
    renderHook(() => useLocationOverlay(map, false, vi.fn()));
    expect(mock.mapLayerCalls).toHaveLength(0);
  });
});

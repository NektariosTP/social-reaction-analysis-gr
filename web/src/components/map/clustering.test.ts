import { describe, expect, it } from "vitest";
import { buildClusterIndex, getClusterPoints } from "./clustering";
import type { GeoJsonFeature } from "../../client/types.gen";

function feature(id: string, lon: number, lat: number): GeoJsonFeature {
  return {
    geometry: { coordinates: [lon, lat] },
    properties: {
      id,
      action_forms: [],
      thematic_fields: [],
      channel: null,
      intensity: null,
      article_count: 1,
    },
  };
}

describe("clustering", () => {
  it("keeps distinct, far-apart events separate at high zoom", () => {
    const index = buildClusterIndex([feature("a", 23.7, 38.5), feature("b", 21.0, 39.5)]);
    const points = getClusterPoints(index, [-180, -85, 180, 85], 14);
    expect(points).toHaveLength(2);
    expect(points.every((p) => !p.isCluster)).toBe(true);
  });

  it("merges nearby events into a single aggregate point at low zoom", () => {
    const index = buildClusterIndex([
      feature("a", 23.7, 38.5),
      feature("b", 23.701, 38.501),
      feature("c", 23.702, 38.502),
    ]);
    const points = getClusterPoints(index, [-180, -85, 180, 85], 2);
    expect(points).toHaveLength(1);
    expect(points[0].isCluster).toBe(true);
    expect(points[0].pointCount).toBe(3);
  });

  it("exposes the original feature on leaf (non-cluster) points", () => {
    const index = buildClusterIndex([feature("solo", 23.7, 38.5)]);
    const points = getClusterPoints(index, [-180, -85, 180, 85], 14);
    expect(points[0].isCluster).toBe(false);
    expect(points[0].feature?.properties.id).toBe("solo");
  });
});

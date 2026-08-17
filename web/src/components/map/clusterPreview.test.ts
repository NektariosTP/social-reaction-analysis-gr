import { describe, expect, it } from "vitest";
import type { GeoJsonFeature } from "../../client/types.gen";
import {
  ORBIT_CAP,
  scoreFeature,
  buildClusterPreview,
} from "./clusterPreview";

function feat(id: string, articleCount: number, intensity: string | null): GeoJsonFeature {
  return {
    geometry: { coordinates: [23.7, 38.0] },
    properties: {
      id,
      action_forms: [],
      thematic_fields: [],
      channel: null,
      intensity,
      article_count: articleCount,
    },
  };
}

describe("scoreFeature", () => {
  it("combines article_count with intensityLevel * 5", () => {
    // level 3 → 3*5 + 4 = 19
    expect(scoreFeature(feat("a", 4, "Βίαιη/Συγκρουσιακή"))).toBe(19);
    // level 1 → 1*5 + 2 = 7
    expect(scoreFeature(feat("b", 2, "Ειρηνική"))).toBe(7);
  });

  it("treats missing intensity as level 0", () => {
    expect(scoreFeature(feat("c", 6, null))).toBe(6);
  });
});

describe("buildClusterPreview", () => {
  it("shows everything with no remainder when leaves fit within center + cap", () => {
    const leaves = [feat("a", 1, null), feat("b", 2, null), feat("c", 3, null)];
    const preview = buildClusterPreview(leaves, 3);
    expect(preview.orbiters).toHaveLength(2);
    expect(preview.remainderCount).toBe(0);
  });

  it("caps orbiters and computes remainder from pointCount", () => {
    // 8 leaves, pointCount 8 → 1 center + 5 orbiters + remainder 2
    const leaves = Array.from({ length: 8 }, (_, i) => feat(`e${i}`, i + 1, null));
    const preview = buildClusterPreview(leaves, 8);
    expect(preview.orbiters).toHaveLength(ORBIT_CAP);
    expect(preview.remainderCount).toBe(8 - (1 + ORBIT_CAP)); // 2
  });

  it("uses pointCount (not sample size) for the remainder", () => {
    // sample of 6 leaves but the true cluster has 40 members
    const leaves = Array.from({ length: 6 }, (_, i) => feat(`e${i}`, i + 1, null));
    const preview = buildClusterPreview(leaves, 40);
    expect(preview.orbiters).toHaveLength(ORBIT_CAP);
    expect(preview.remainderCount).toBe(40 - 6); // 34
  });

  it("picks the highest-scoring leaf as center and orders orbiters descending", () => {
    const leaves = [feat("low", 1, null), feat("high", 9, null), feat("mid", 5, null)];
    const preview = buildClusterPreview(leaves, 3);
    expect(preview.center.properties.id).toBe("high");
    expect(preview.orbiters.map((o) => o.properties.id)).toEqual(["mid", "low"]);
  });
});

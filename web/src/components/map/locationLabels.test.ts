import { describe, expect, it } from "vitest";
import type { GeoJsonFeature } from "../../client/types.gen";
import { primaryLocationLabel, secondaryLocationLabels } from "./locationLabels";

function feat(id: string, locations: unknown[]): GeoJsonFeature {
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
      locations: locations as any,
    },
  } as GeoJsonFeature;
}

// Whole-world bbox: [minLon, minLat, maxLon, maxLat].
const WORLD: [number, number, number, number] = [-180, -85, 180, 85];

const primary = { lat: 38.0, lon: 23.7, label: "Αθήνα", is_primary: true };
const unnamedPrimary = { lat: 38.0, lon: 23.7, label: null, is_primary: true };
const sat1 = { lat: 40.64, lon: 22.94, label: "Θεσσαλονίκη", is_primary: false };
const sat2 = { lat: 35.34, lon: 25.14, label: null, is_primary: false };

describe("primaryLocationLabel", () => {
  it("returns the primary location's admin-saved name", () => {
    expect(primaryLocationLabel(feat("a", [primary]).properties)).toBe("Αθήνα");
  });

  it("returns undefined when there is no locations array", () => {
    expect(primaryLocationLabel({ locations: undefined })).toBeUndefined();
  });

  it("returns undefined when the primary has no label", () => {
    expect(primaryLocationLabel(feat("a", [unnamedPrimary]).properties)).toBeUndefined();
  });
});

describe("secondaryLocationLabels", () => {
  it("returns one label per named secondary in view", () => {
    const out = secondaryLocationLabels([feat("a", [primary, sat1, sat2])], WORLD);
    expect(out).toEqual([{ eventId: "a", coordinates: [sat1.lon, sat1.lat], text: "Θεσσαλονίκη" }]);
  });

  it("excludes the primary location", () => {
    const out = secondaryLocationLabels([feat("a", [primary, sat1])], WORLD);
    expect(out.every((l) => l.coordinates[1] !== primary.lat)).toBe(true);
  });

  it("skips single-location events (no secondaries to label)", () => {
    const out = secondaryLocationLabels([feat("a", [primary])], WORLD);
    expect(out).toHaveLength(0);
  });

  it("keeps a secondary's label even when the primary is outside the bbox", () => {
    // Regression: the label must follow the secondary's own position, not the
    // primary's — a secondary in view keeps its subtitle while the primary is
    // panned off screen. Bbox around Thessaloniki only (excludes Athens primary).
    const thessalonikiBox: [number, number, number, number] = [22.5, 40.3, 23.3, 41.0];
    const out = secondaryLocationLabels([feat("a", [primary, sat1])], thessalonikiBox);
    expect(out).toHaveLength(1);
    expect(out[0].text).toBe("Θεσσαλονίκη");
  });

  it("drops a secondary whose own coordinate is outside the bbox", () => {
    // Bbox around Athens only — Thessaloniki secondary is off screen.
    const athensBox: [number, number, number, number] = [23.5, 37.8, 24.0, 38.2];
    const out = secondaryLocationLabels([feat("a", [primary, sat1])], athensBox);
    expect(out).toHaveLength(0);
  });
});

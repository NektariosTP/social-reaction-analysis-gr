import { describe, expect, it } from "vitest";
import type { GeoJsonFeature } from "../../client/types.gen";
import { buildLocationOverlay } from "./eventLocations";
import { intensityColor } from "./bubbleColors";

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

const primary = { lat: 38.0, lon: 23.7, label: "Αθήνα", is_primary: true };
const sat1 = { lat: 40.64, lon: 22.94, label: "Θεσσαλονίκη", is_primary: false };
const sat2 = { lat: 35.34, lon: 25.14, label: "Ηράκλειο", is_primary: false };

describe("buildLocationOverlay", () => {
  it("skips single-location events", () => {
    const out = buildLocationOverlay([feat("a", [primary])], []);
    expect(out.secondaries.features).toHaveLength(0);
    expect(out.connectors.features).toHaveLength(0);
  });

  it("still emits the overlay when the primary is clustered / off-screen", () => {
    // Regression: the overlay used to be gated on the primary being rendered as
    // its own (un-clustered, in-viewport) marker, so satellites vanished the
    // moment the primary joined a cluster or panned off screen.
    const out = buildLocationOverlay([feat("a", [primary, sat1])], []);
    expect(out.secondaries.features).toHaveLength(1);
    expect(out.connectors.features).toHaveLength(1);
  });

  it("emits one secondary + connector per satellite", () => {
    const out = buildLocationOverlay([feat("a", [primary, sat1, sat2])], []);
    expect(out.secondaries.features).toHaveLength(2);
    expect(out.connectors.features).toHaveLength(2);
  });

  it("orders connector coords secondary -> primary", () => {
    const out = buildLocationOverlay([feat("a", [primary, sat1])], []);
    const line = out.connectors.features[0].geometry as GeoJSON.LineString;
    expect(line.coordinates[0]).toEqual([sat1.lon, sat1.lat]);
    expect(line.coordinates[1]).toEqual([primary.lon, primary.lat]);
  });

  it("marks active and colours by intensity", () => {
    const out = buildLocationOverlay([feat("a", [primary, sat1])], ["a"]);
    expect(out.secondaries.features[0].properties).toMatchObject({
      eventId: "a",
      active: true,
      color: intensityColor("Ειρηνική"),
    });
  });

  it("treats an event as inactive when it isn't in activeIds", () => {
    const out = buildLocationOverlay([feat("a", [primary, sat1])], ["b", null]);
    expect(out.secondaries.features[0].properties).toMatchObject({ active: false });
  });

  it("activates via any id in activeIds (e.g. hover + selection together)", () => {
    const out = buildLocationOverlay([feat("a", [primary, sat1])], [null, "a"]);
    expect(out.secondaries.features[0].properties).toMatchObject({ active: true });
  });
});

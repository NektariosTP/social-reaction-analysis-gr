import type { GeoJsonFeature } from "../../client/types.gen";
import { intensityColor } from "./bubbleColors";

export interface LocationOverlay {
  secondaries: GeoJSON.FeatureCollection;
  connectors: GeoJSON.FeatureCollection;
}

interface Loc {
  lat: number;
  lon: number;
  label?: string | null;
  is_primary: boolean;
}

/**
 * Derive satellite circles + connector lines for multi-location events.
 *
 * Every multi-location event contributes, regardless of viewport or clustering.
 * We deliberately do NOT gate on whether the primary is currently rendered as
 * its own marker: a secondary can be on screen while the primary is panned off
 * (the connector just runs off-screen), and the primary is often swallowed into
 * a nearby cluster — in both cases the satellites/connectors must still show.
 * Connectors anchor to the event's own primary coordinate (≈ the cluster's
 * position when it is clustered), so they don't dangle in empty space.
 */
export function buildLocationOverlay(
  features: GeoJsonFeature[],
  selectedId: string | null,
): LocationOverlay {
  const secondaries: GeoJSON.Feature[] = [];
  const connectors: GeoJSON.Feature[] = [];

  for (const f of features) {
    const id = f.properties.id;
    const locations = (f.properties.locations ?? []) as Loc[];
    if (locations.length < 2) continue;

    const primary = locations.find((l) => l.is_primary) ?? {
      lon: (f.geometry.coordinates as number[])[0],
      lat: (f.geometry.coordinates as number[])[1],
      is_primary: true,
    };
    const color = intensityColor(f.properties.intensity);
    const selected = id === selectedId;
    const props = { eventId: id, selected, color };

    for (const loc of locations) {
      if (loc.is_primary) continue;
      secondaries.push({
        type: "Feature",
        geometry: { type: "Point", coordinates: [loc.lon, loc.lat] },
        properties: props,
      });
      connectors.push({
        type: "Feature",
        geometry: {
          type: "LineString",
          coordinates: [
            [loc.lon, loc.lat],
            [primary.lon, primary.lat],
          ],
        },
        properties: props,
      });
    }
  }

  return {
    secondaries: { type: "FeatureCollection", features: secondaries },
    connectors: { type: "FeatureCollection", features: connectors },
  };
}

import type { GeoJsonFeature, GeoJsonProperties } from "../../client/types.gen";

/** Zoom at/above which location-name subtitles appear. Below it (country/region
 * overview) the map stays clean; ~11 is "focused on a city/area". */
export const LABEL_MIN_ZOOM = 11;

interface Loc {
  lat: number;
  lon: number;
  label?: string | null;
  is_primary: boolean;
}

export interface SecondaryLabelPoint {
  eventId: string;
  coordinates: [number, number];
  text: string;
}

/** The admin-saved name of an event's primary location, or undefined if unset. */
export function primaryLocationLabel(
  properties: Pick<GeoJsonProperties, "locations">,
): string | undefined {
  const locations = (properties.locations ?? []) as Loc[];
  const primary = locations.find((l) => l.is_primary);
  return primary?.label ?? undefined;
}

/**
 * One label per named secondary location whose OWN coordinate falls inside
 * `bbox`. Deliberately independent of whether the event's primary is on screen
 * or folded into a cluster: a secondary's subtitle must stay put when the
 * primary is panned off or clustered (matches the always-on secondaries overlay
 * in useLocationOverlay). Caller gates the whole call on zoom (LABEL_MIN_ZOOM).
 */
export function secondaryLocationLabels(
  features: GeoJsonFeature[],
  bbox: [number, number, number, number],
): SecondaryLabelPoint[] {
  const [minLon, minLat, maxLon, maxLat] = bbox;
  const out: SecondaryLabelPoint[] = [];
  for (const f of features) {
    const locations = (f.properties.locations ?? []) as Loc[];
    // Only multi-location events have secondaries (mirrors buildLocationOverlay).
    if (locations.length < 2) continue;
    for (const loc of locations) {
      if (loc.is_primary || !loc.label) continue;
      if (loc.lon < minLon || loc.lon > maxLon || loc.lat < minLat || loc.lat > maxLat) continue;
      out.push({ eventId: f.properties.id, coordinates: [loc.lon, loc.lat], text: loc.label });
    }
  }
  return out;
}

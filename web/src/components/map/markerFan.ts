import { MARKER_DIAMETER } from "./markerStyle";

/**
 * Fan-out for markers that share the exact same coordinates.
 *
 * The geocoder often pins many events to a single city centroid, so once the
 * map is zoomed past the cluster maxZoom those events un-cluster and render as
 * individual bubbles stacked precisely on top of each other. Rather than let
 * them overlap, we spread each coincident group into a centred grid using
 * maplibre's pixel `offset` — screen-space, so the bubble size and spacing stay
 * constant at any zoom.
 */

export const MARKER_FAN_PER_ROW = 3;
const MARKER_FAN_GAP = 6;
/** Distance in px between adjacent bubble centres in the fan grid. */
export const MARKER_FAN_STEP = MARKER_DIAMETER + MARKER_FAN_GAP;

/**
 * Pixel offsets that lay `count` markers out in a grid of at most `perRow`
 * columns, centred on the shared point. Index i → [dx, dy] for the i-th marker.
 * Each row is horizontally centred and the whole block is vertically centred.
 */
export function fanOutOffsets(
  count: number,
  perRow: number = MARKER_FAN_PER_ROW,
  step: number = MARKER_FAN_STEP,
): [number, number][] {
  const rows = Math.ceil(count / perRow);
  const offsets: [number, number][] = [];
  for (let i = 0; i < count; i++) {
    const row = Math.floor(i / perRow);
    const rowStart = row * perRow;
    const rowCount = Math.min(perRow, count - rowStart);
    const col = i - rowStart;
    const dx = (col - (rowCount - 1) / 2) * step;
    const dy = (row - (rows - 1) / 2) * step;
    offsets.push([dx, dy]);
  }
  return offsets;
}

const coordKey = (c: [number, number]) => `${c[0]},${c[1]}`;

/**
 * Map from marker id → fan offset, for the subset of `items` that share exact
 * coordinates with at least one other marker. Unique-location markers are
 * absent from the map (callers treat that as a [0, 0] offset). Offsets within a
 * group follow input order so the layout is stable across renders.
 */
export function fanOffsetsByCoincidence(
  items: { id: string; coordinates: [number, number] }[],
  perRow: number = MARKER_FAN_PER_ROW,
  step: number = MARKER_FAN_STEP,
): Map<string, [number, number]> {
  const groups = new Map<string, string[]>();
  for (const item of items) {
    const key = coordKey(item.coordinates);
    const group = groups.get(key);
    if (group) group.push(item.id);
    else groups.set(key, [item.id]);
  }

  const result = new Map<string, [number, number]>();
  for (const ids of groups.values()) {
    if (ids.length <= 1) continue;
    const offsets = fanOutOffsets(ids.length, perRow, step);
    ids.forEach((id, i) => result.set(id, offsets[i]));
  }
  return result;
}

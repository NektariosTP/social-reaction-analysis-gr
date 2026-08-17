import type { GeoJsonFeature } from "../../client/types.gen";
import { intensityLevel } from "../../i18n";

export const ORBIT_CAP = 5;
export const LEAF_SAMPLE_SIZE = 40;

/** Combined importance score: article volume plus a weighted intensity bump. */
export function scoreFeature(feature: GeoJsonFeature): number {
  const level = intensityLevel(feature.properties.intensity) ?? 0;
  return (feature.properties.article_count ?? 0) + level * 5;
}

export interface ClusterPreview {
  center: GeoJsonFeature;
  orbiters: GeoJsonFeature[]; // rank order, most important first, length <= cap
  remainderCount: number; // 0 if the whole cluster is shown
}

/**
 * `leaves` is a bounded sample from `index.getLeaves(clusterId, LEAF_SAMPLE_SIZE)` — ranking is
 * done against that sample, not the full cluster, to keep this O(1) per cluster regardless of
 * cluster size. `pointCount` is Supercluster's exact total member count (from the cluster's own
 * properties), used only to size the remainder pill correctly even when the true top-N isn't in
 * the sample.
 *
 * Precondition (not defensively checked): leaves.length >= 1, guaranteed by the caller — a
 * Supercluster cluster point always has pointCount >= 2 and getLeaves with a positive limit
 * always returns at least one leaf.
 */
export function buildClusterPreview(
  leaves: GeoJsonFeature[],
  pointCount: number,
  cap: number = ORBIT_CAP,
): ClusterPreview {
  const ranked = [...leaves].sort((a, b) => scoreFeature(b) - scoreFeature(a));
  const center = ranked[0];
  const orbiters = ranked.slice(1, 1 + cap);
  const shown = 1 + orbiters.length;
  const remainderCount = Math.max(0, pointCount - shown);
  return { center, orbiters, remainderCount };
}

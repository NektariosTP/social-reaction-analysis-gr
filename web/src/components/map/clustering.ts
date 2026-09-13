import Supercluster from "supercluster";
import type { GeoJsonFeature } from "../../client/types.gen";

export interface ClusterPoint {
  isCluster: boolean;
  clusterId?: number;
  pointCount?: number;
  coordinates: [number, number];
  feature?: GeoJsonFeature;
}

interface IndexedProperties {
  __feature: GeoJsonFeature;
}

export function buildClusterIndex(features: GeoJsonFeature[]) {
  const index = new Supercluster<IndexedProperties>({ radius: 50, maxZoom: 14 });
  index.load(
    features
      .filter((f) => f.geometry.coordinates.length === 2)
      .map((f) => ({
        type: "Feature" as const,
        properties: { __feature: f },
        geometry: {
          type: "Point" as const,
          coordinates: f.geometry.coordinates as [number, number],
        },
      })),
  );
  return index;
}

/** The lowest integer zoom at which `eventId` renders as its own marker rather
 * than being folded into a cluster with neighbouring events. Used by "View on
 * map" so the target event is actually singled out, not left inside a cluster
 * bubble. Returns `maxZoom` if it never fully separates (e.g. co-located events). */
export function getEventIsolationZoom(
  index: Supercluster<IndexedProperties>,
  eventId: string,
  [lng, lat]: [number, number],
  maxZoom = 15,
): number {
  const pad = 0.02;
  const bbox: [number, number, number, number] = [lng - pad, lat - pad, lng + pad, lat + pad];
  for (let z = 0; z <= maxZoom; z++) {
    const isolated = index.getClusters(bbox, z).some(
      (c) =>
        !("cluster" in c.properties && c.properties.cluster) &&
        c.properties.__feature.properties.id === eventId,
    );
    if (isolated) return z;
  }
  return maxZoom;
}

export function getClusterPoints(
  index: Supercluster<IndexedProperties>,
  bbox: [number, number, number, number],
  zoom: number,
): ClusterPoint[] {
  return index.getClusters(bbox, Math.round(zoom)).map((c) => {
    const coordinates = c.geometry.coordinates as [number, number];
    if ("cluster" in c.properties && c.properties.cluster) {
      return {
        isCluster: true,
        clusterId: c.properties.cluster_id,
        pointCount: c.properties.point_count,
        coordinates,
      };
    }
    return {
      isCluster: false,
      coordinates,
      feature: c.properties.__feature,
    };
  });
}

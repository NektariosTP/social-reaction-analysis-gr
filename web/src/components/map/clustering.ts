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

export function getClusterPoints(
  index: Supercluster<IndexedProperties>,
  bbox: [number, number, number, number],
  zoom: number,
): ClusterPoint[] {
  return index.getClusters(bbox, Math.round(zoom)).map((c) => {
    const coordinates = c.geometry.coordinates as [number, number];
    if (c.properties.cluster) {
      return {
        isCluster: true,
        clusterId: c.properties.cluster_id as number,
        pointCount: c.properties.point_count as number,
        coordinates,
      };
    }
    return {
      isCluster: false,
      coordinates,
      feature: (c.properties as unknown as IndexedProperties).__feature,
    };
  });
}

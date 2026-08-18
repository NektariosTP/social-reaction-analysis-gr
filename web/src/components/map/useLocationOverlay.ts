import { useEffect, useRef } from "react";
import type maplibregl from "maplibre-gl";
import type { GeoJsonFeature } from "../../client/types.gen";
import { buildLocationOverlay } from "./eventLocations";

const CONNECTOR_SOURCE = "event-connectors-src";
const SECONDARY_SOURCE = "event-secondaries-src";
const CONNECTOR_LAYER = "event-connectors";
const SECONDARY_LAYER = "event-secondaries";

const EMPTY: GeoJSON.FeatureCollection = { type: "FeatureCollection", features: [] };

// Ant-trail dash patterns, cycled to make dashes flow toward the primary.
const DASH_SEQUENCE: number[][] = [
  [0, 4, 3], [0.5, 4, 2.5], [1, 4, 2], [1.5, 4, 1.5],
  [2, 4, 1], [2.5, 4, 0.5], [3, 4, 0], [0, 0.5, 3, 3.5],
  [0, 1, 3, 3], [0, 1.5, 3, 2.5], [0, 2, 3, 2], [0, 2.5, 3, 1.5],
  [0, 3, 3, 1], [0, 3.5, 3, 0.5],
];

export interface LocationOverlayHandle {
  updateOverlay(features: GeoJsonFeature[], selectedId: string | null): void;
}

export function useLocationOverlay(
  map: maplibregl.Map | null,
  styleLoaded: boolean,
  onSelectEvent: (id: string) => void,
): LocationOverlayHandle {
  const hasDataRef = useRef(false);
  const onSelectRef = useRef(onSelectEvent);
  useEffect(() => {
    onSelectRef.current = onSelectEvent;
  }, [onSelectEvent]);

  useEffect(() => {
    if (!map || !styleLoaded) return;

    map.addSource(CONNECTOR_SOURCE, { type: "geojson", data: EMPTY });
    map.addSource(SECONDARY_SOURCE, { type: "geojson", data: EMPTY });

    // Connectors first so circles paint above the lines.
    map.addLayer({
      id: CONNECTOR_LAYER,
      type: "line",
      source: CONNECTOR_SOURCE,
      paint: {
        "line-color": ["get", "color"],
        // Keep the unselected state clearly legible (not a faint ghost) while
        // still visibly emphasising the selected event.
        "line-opacity": ["case", ["get", "selected"], 0.95, 0.65],
        "line-width": ["case", ["get", "selected"], 3, 2],
        "line-dasharray": [0, 4, 3],
      },
    });
    map.addLayer({
      id: SECONDARY_LAYER,
      type: "circle",
      source: SECONDARY_SOURCE,
      paint: {
        "circle-color": ["get", "color"],
        "circle-radius": ["case", ["get", "selected"], 8, 7],
        "circle-opacity": ["case", ["get", "selected"], 0.95, 0.8],
        "circle-stroke-width": 1.5,
        "circle-stroke-color": "#ffffff",
        "circle-stroke-opacity": ["case", ["get", "selected"], 1, 0.9],
      },
    });

    const handleClick = (e: maplibregl.MapLayerMouseEvent) => {
      const id = e.features?.[0]?.properties?.eventId;
      if (typeof id === "string") onSelectRef.current(id);
    };
    const enter = () => {
      map.getCanvas().style.cursor = "pointer";
    };
    const leave = () => {
      map.getCanvas().style.cursor = "";
    };
    map.on("click", SECONDARY_LAYER, handleClick);
    map.on("mouseenter", SECONDARY_LAYER, enter);
    map.on("mouseleave", SECONDARY_LAYER, leave);

    // Ant-trail animation (~15fps), only while connectors are present.
    let raf = 0;
    let step = 0;
    let last = 0;
    const tick = (t: number) => {
      raf = requestAnimationFrame(tick);
      if (!hasDataRef.current) return;
      if (t - last < 66) return;
      last = t;
      step = (step + 1) % DASH_SEQUENCE.length;
      if (map.getLayer(CONNECTOR_LAYER)) {
        map.setPaintProperty(CONNECTOR_LAYER, "line-dasharray", DASH_SEQUENCE[step]);
      }
    };
    raf = requestAnimationFrame(tick);

    return () => {
      cancelAnimationFrame(raf);
      // React runs unmount cleanups in mount order, and MapView's map-init
      // effect (registered first) calls map.remove() before this one runs when
      // the whole MapView unmounts (e.g. navigating back off the cluster-detail
      // mini-map). Touching a removed map throws ("reading 'getLayer' of
      // undefined") — its layers/sources are already gone anyway, so bail.
      if ((map as unknown as { _removed?: boolean })._removed) return;
      if (map.getLayer(SECONDARY_LAYER)) map.removeLayer(SECONDARY_LAYER);
      if (map.getLayer(CONNECTOR_LAYER)) map.removeLayer(CONNECTOR_LAYER);
      if (map.getSource(SECONDARY_SOURCE)) map.removeSource(SECONDARY_SOURCE);
      if (map.getSource(CONNECTOR_SOURCE)) map.removeSource(CONNECTOR_SOURCE);
    };
  }, [map, styleLoaded]);

  return {
    updateOverlay(features, selectedId) {
      if (!map) return;
      const { secondaries, connectors } = buildLocationOverlay(features, selectedId);
      hasDataRef.current = connectors.features.length > 0;
      (map.getSource(CONNECTOR_SOURCE) as maplibregl.GeoJSONSource | undefined)?.setData(connectors);
      (map.getSource(SECONDARY_SOURCE) as maplibregl.GeoJSONSource | undefined)?.setData(secondaries);
    },
  };
}

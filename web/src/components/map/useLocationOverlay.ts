import { useEffect, useRef } from "react";
import type maplibregl from "maplibre-gl";
import type { GeoJsonFeature } from "../../client/types.gen";
import { buildLocationOverlay } from "./eventLocations";

const CONNECTOR_SOURCE = "event-connectors-src";
const SECONDARY_SOURCE = "event-secondaries-src";
const CONNECTOR_LAYER = "event-connectors";
const CONNECTOR_ACTIVE_LAYER = "event-connectors-active";
const SECONDARY_LAYER = "event-secondaries";
const SECONDARY_ACTIVE_LAYER = "event-secondaries-active";

const EMPTY: GeoJSON.FeatureCollection = { type: "FeatureCollection", features: [] };

// Ant-trail dash patterns, cycled to make dashes flow toward the primary.
// Only the active (hovered/selected) connector layer ever animates through
// these — every other connector stays on the first frame so the map isn't a
// field of crawling lines when several multi-location events are on screen.
const DASH_SEQUENCE: number[][] = [
  [0, 4, 3], [0.5, 4, 2.5], [1, 4, 2], [1.5, 4, 1.5],
  [2, 4, 1], [2.5, 4, 0.5], [3, 4, 0], [0, 0.5, 3, 3.5],
  [0, 1, 3, 3], [0, 1.5, 3, 2.5], [0, 2, 3, 2], [0, 2.5, 3, 1.5],
  [0, 3, 3, 1], [0, 3.5, 3, 0.5],
];
const STATIC_DASH = DASH_SEQUENCE[0];

export interface LocationOverlayHandle {
  updateOverlay(
    features: GeoJsonFeature[],
    activeIds: ReadonlyArray<string | null | undefined>,
  ): void;
}

export function useLocationOverlay(
  map: maplibregl.Map | null,
  styleLoaded: boolean,
  onSelectEvent: (id: string) => void,
): LocationOverlayHandle {
  const hasActiveRef = useRef(false);
  const onSelectRef = useRef(onSelectEvent);
  useEffect(() => {
    onSelectRef.current = onSelectEvent;
  }, [onSelectEvent]);

  useEffect(() => {
    if (!map || !styleLoaded) return;

    map.addSource(CONNECTOR_SOURCE, { type: "geojson", data: EMPTY });
    map.addSource(SECONDARY_SOURCE, { type: "geojson", data: EMPTY });

    // Static layers first so the active layers (drawn per-event, on
    // hover/select) always paint on top of the muted crowd.
    map.addLayer({
      id: CONNECTOR_LAYER,
      type: "line",
      source: CONNECTOR_SOURCE,
      filter: ["!", ["get", "active"]],
      paint: {
        "line-color": ["get", "color"],
        "line-opacity": 0.65,
        "line-width": 2,
        "line-dasharray": STATIC_DASH,
      },
    });
    map.addLayer({
      id: CONNECTOR_ACTIVE_LAYER,
      type: "line",
      source: CONNECTOR_SOURCE,
      filter: ["get", "active"],
      paint: {
        "line-color": ["get", "color"],
        "line-opacity": 0.95,
        "line-width": 3,
        "line-dasharray": STATIC_DASH,
      },
    });
    map.addLayer({
      id: SECONDARY_LAYER,
      type: "circle",
      source: SECONDARY_SOURCE,
      filter: ["!", ["get", "active"]],
      paint: {
        "circle-color": ["get", "color"],
        "circle-radius": 7,
        "circle-opacity": 0.8,
        "circle-stroke-width": 1.5,
        "circle-stroke-color": "#ffffff",
        "circle-stroke-opacity": 0.9,
      },
    });
    map.addLayer({
      id: SECONDARY_ACTIVE_LAYER,
      type: "circle",
      source: SECONDARY_SOURCE,
      filter: ["get", "active"],
      paint: {
        "circle-color": ["get", "color"],
        "circle-radius": 8,
        "circle-opacity": 0.95,
        "circle-stroke-width": 1.5,
        "circle-stroke-color": "#ffffff",
        "circle-stroke-opacity": 1,
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
    for (const layer of [SECONDARY_LAYER, SECONDARY_ACTIVE_LAYER]) {
      map.on("click", layer, handleClick);
      map.on("mouseenter", layer, enter);
      map.on("mouseleave", layer, leave);
    }

    // Ant-trail animation (~15fps), only while an active connector exists.
    let raf = 0;
    let step = 0;
    let last = 0;
    const tick = (t: number) => {
      raf = requestAnimationFrame(tick);
      if (!hasActiveRef.current) return;
      if (t - last < 66) return;
      last = t;
      step = (step + 1) % DASH_SEQUENCE.length;
      if (map.getLayer(CONNECTOR_ACTIVE_LAYER)) {
        map.setPaintProperty(CONNECTOR_ACTIVE_LAYER, "line-dasharray", DASH_SEQUENCE[step]);
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
      for (const id of [SECONDARY_ACTIVE_LAYER, SECONDARY_LAYER, CONNECTOR_ACTIVE_LAYER, CONNECTOR_LAYER]) {
        if (map.getLayer(id)) map.removeLayer(id);
      }
      if (map.getSource(SECONDARY_SOURCE)) map.removeSource(SECONDARY_SOURCE);
      if (map.getSource(CONNECTOR_SOURCE)) map.removeSource(CONNECTOR_SOURCE);
    };
  }, [map, styleLoaded]);

  return {
    updateOverlay(features, activeIds) {
      if (!map) return;
      const { secondaries, connectors } = buildLocationOverlay(features, activeIds);
      hasActiveRef.current = connectors.features.some((f) => f.properties?.active === true);
      (map.getSource(CONNECTOR_SOURCE) as maplibregl.GeoJSONSource | undefined)?.setData(connectors);
      (map.getSource(SECONDARY_SOURCE) as maplibregl.GeoJSONSource | undefined)?.setData(secondaries);
    },
  };
}

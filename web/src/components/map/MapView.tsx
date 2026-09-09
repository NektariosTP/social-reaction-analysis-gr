import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import type { GeoJsonFeature } from "../../client/types.gen";
import { buildClusterIndex, getClusterPoints } from "./clustering";
import { createMarkerElement, createClusterMarkerElement } from "./markerElement";
import { buildClusterPreview, LEAF_SAMPLE_SIZE } from "./clusterPreview";
import { ClusterPopup } from "./ClusterPopup";
import { useLocationOverlay } from "./useLocationOverlay";
import styles from "./MapView.module.css";

const MAPTILER_KEY = import.meta.env.VITE_MAPTILER_KEY as string | undefined;
const STYLE_URL = MAPTILER_KEY
  ? `https://api.maptiler.com/maps/streets-v2/style.json?key=${MAPTILER_KEY}`
  : "https://demotiles.maplibre.org/style.json";

const GREECE_CENTER: [number, number] = [23.7, 38.5];
const GREECE_ZOOM = 6.5;
const GREECE_MIN_ZOOM = 5.6;

interface MapViewProps {
  features: GeoJsonFeature[];
  onSelectEvent: (id: string) => void;
  selectedId?: string | null;
  flyTo?: { center: [number, number]; zoom?: number } | null;
  onReadMorePopup?: (id: string) => void;
  onClosePopup?: () => void;
  /** Width (px) of UI chrome overlaying the left edge of the map (e.g. the floating sidebar). */
  obstructedLeft?: number;
}

export function MapView({
  features,
  onSelectEvent,
  selectedId,
  flyTo,
  onReadMorePopup,
  onClosePopup,
  obstructedLeft = 0,
}: MapViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markersRef = useRef<maplibregl.Marker[]>([]);
  const [mapInstance, setMapInstance] = useState<maplibregl.Map | null>(null);
  const [styleLoaded, setStyleLoaded] = useState(false);
  const onSelectEventRef = useRef(onSelectEvent);
  useEffect(() => {
    onSelectEventRef.current = onSelectEvent;
  }, [onSelectEvent]);
  const featuresRef = useRef(features);
  useEffect(() => {
    featuresRef.current = features;
  }, [features]);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: STYLE_URL,
      center: GREECE_CENTER,
      zoom: GREECE_ZOOM,
      minZoom: GREECE_MIN_ZOOM,
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "bottom-right");
    const fullscreenTarget = document.getElementById("root") ?? undefined;
    map.addControl(
      new maplibregl.FullscreenControl({ container: fullscreenTarget }),
      "bottom-right",
    );
    mapRef.current = map;
    setMapInstance(map);
    map.once("load", () => setStyleLoaded(true));
    return () => {
      map.remove();
      mapRef.current = null;
      setMapInstance(null);
      setStyleLoaded(false);
    };
  }, []);

  const overlay = useLocationOverlay(mapInstance, styleLoaded, onSelectEvent);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !styleLoaded) return;

    const index = buildClusterIndex(features);
    let animateNextEntrance = false;

    const render = () => {
      const animateEntrance = animateNextEntrance;
      animateNextEntrance = false;
      markersRef.current.forEach((m) => m.remove());
      const bounds = map.getBounds().toArray();
      const bbox: [number, number, number, number] = [
        bounds[0][0],
        bounds[0][1],
        bounds[1][0],
        bounds[1][1],
      ];
      const points = getClusterPoints(index, bbox, map.getZoom());

      markersRef.current = points.map((point) => {
        if (point.isCluster) {
          const leaves = index
            .getLeaves(point.clusterId!, LEAF_SAMPLE_SIZE)
            .map((l) => l.properties.__feature);
          const preview = buildClusterPreview(leaves, point.pointCount ?? 0);
          const el = createClusterMarkerElement(preview, animateEntrance);
          el.addEventListener("click", () => {
            const zoom = index.getClusterExpansionZoom(point.clusterId!);
            map.easeTo({ center: point.coordinates, zoom });
          });
          return new maplibregl.Marker({ element: el, anchor: "center" })
            .setLngLat(point.coordinates)
            .addTo(map);
        }
        const feature = point.feature!;
        const el = createMarkerElement(
          feature.properties,
          feature.properties.article_count,
          feature.properties.id === selectedId,
        );
        el.addEventListener("click", () => onSelectEventRef.current(feature.properties.id));
        return new maplibregl.Marker({ element: el, anchor: "center" })
          .setLngLat(point.coordinates)
          .addTo(map);
      });

      // Overlay covers every multi-location event regardless of viewport or
      // clustering (see buildLocationOverlay) — it isn't derived from `points`.
      overlay.updateOverlay(featuresRef.current, selectedId ?? null);
    };

    const handleZoomStart = () => {
      animateNextEntrance = true;
      containerRef.current?.classList.add(styles.clusterZooming);
    };
    const handleZoomEnd = () => {
      containerRef.current?.classList.remove(styles.clusterZooming);
      render();
    };

    render();
    map.on("moveend", render);
    map.on("zoomstart", handleZoomStart);
    map.on("zoomend", handleZoomEnd);

    return () => {
      map.off("moveend", render);
      map.off("zoomstart", handleZoomStart);
      map.off("zoomend", handleZoomEnd);
      containerRef.current?.classList.remove(styles.clusterZooming);
      markersRef.current.forEach((m) => m.remove());
      markersRef.current = [];
    };
  }, [features, selectedId, styleLoaded, overlay]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !flyTo) return;
    map.flyTo({ center: flyTo.center, zoom: flyTo.zoom ?? 8 });
  }, [flyTo]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !selectedId) return;
    const feature = featuresRef.current.find((f) => f.properties.id === selectedId);
    if (!feature) return;
    const [lng, lat] = feature.geometry.coordinates as [number, number];
    map.flyTo({
      center: [lng, lat],
      zoom: Math.max(map.getZoom(), 11),
      offset: [obstructedLeft / 2, 0],
    });
  }, [selectedId, obstructedLeft]);

  const selectedFeature = selectedId
    ? features.find((f) => f.properties.id === selectedId)
    : undefined;

  return (
    <div className={styles.container}>
      <div ref={containerRef} className={styles.map} data-testid="map-canvas" />
      {mapInstance && selectedId && selectedFeature && onClosePopup && (
        <ClusterPopup
          map={mapInstance}
          eventId={selectedId}
          coordinates={selectedFeature.geometry.coordinates as [number, number]}
          onReadMore={onReadMorePopup}
          onClose={onClosePopup}
        />
      )}
    </div>
  );
}

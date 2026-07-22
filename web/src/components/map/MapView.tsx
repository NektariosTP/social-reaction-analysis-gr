import { useEffect, useRef, useState } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import type { GeoJsonFeature } from "../../client/types.gen";
import { buildClusterIndex, getClusterPoints } from "./clustering";
import { createMarkerElement, createClusterMarkerElement } from "./markerElement";
import { ClusterPopup } from "./ClusterPopup";
import styles from "./MapView.module.css";

const MAPTILER_KEY = import.meta.env.VITE_MAPTILER_KEY as string | undefined;
const STYLE_URL = MAPTILER_KEY
  ? `https://api.maptiler.com/maps/streets-v2/style.json?key=${MAPTILER_KEY}`
  : "https://demotiles.maplibre.org/style.json";

const GREECE_CENTER: [number, number] = [23.7, 38.5];
const GREECE_ZOOM = 7.5;
const GREECE_MIN_ZOOM = 5.6;

interface MapViewProps {
  features: GeoJsonFeature[];
  onSelectEvent: (id: string) => void;
  selectedId?: string | null;
  flyTo?: { center: [number, number]; zoom?: number } | null;
  onReadMorePopup?: (id: string) => void;
  onClosePopup?: () => void;
}

export function MapView({
  features,
  onSelectEvent,
  selectedId,
  flyTo,
  onReadMorePopup,
  onClosePopup,
}: MapViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markersRef = useRef<maplibregl.Marker[]>([]);
  const [mapInstance, setMapInstance] = useState<maplibregl.Map | null>(null);
  const onSelectEventRef = useRef(onSelectEvent);
  useEffect(() => {
    onSelectEventRef.current = onSelectEvent;
  }, [onSelectEvent]);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: STYLE_URL,
      center: GREECE_CENTER,
      zoom: GREECE_ZOOM,
      minZoom: GREECE_MIN_ZOOM,
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
    const fullscreenTarget = document.getElementById("root") ?? undefined;
    map.addControl(
      new maplibregl.FullscreenControl({ container: fullscreenTarget }),
      "top-right",
    );
    mapRef.current = map;
    setMapInstance(map);
    return () => {
      map.remove();
      mapRef.current = null;
      setMapInstance(null);
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const index = buildClusterIndex(features);

    const render = () => {
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
          const el = createClusterMarkerElement(point.pointCount ?? 0);
          el.addEventListener("click", () => {
            const zoom = index.getClusterExpansionZoom(point.clusterId!);
            map.easeTo({ center: point.coordinates, zoom });
          });
          return new maplibregl.Marker({ element: el }).setLngLat(point.coordinates).addTo(map);
        }
        const feature = point.feature!;
        const el = createMarkerElement(
          feature.properties,
          feature.properties.article_count,
          feature.properties.id === selectedId,
        );
        el.addEventListener("click", () => onSelectEventRef.current(feature.properties.id));
        return new maplibregl.Marker({ element: el }).setLngLat(point.coordinates).addTo(map);
      });
    };

    const attach = () => {
      render();
      map.on("moveend", render);
      map.on("zoomend", render);
    };

    if (map.isStyleLoaded()) attach();
    else map.once("load", attach);

    return () => {
      map.off("moveend", render);
      map.off("zoomend", render);
      markersRef.current.forEach((m) => m.remove());
      markersRef.current = [];
    };
  }, [features, selectedId]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !flyTo) return;
    map.flyTo({ center: flyTo.center, zoom: flyTo.zoom ?? 8 });
  }, [flyTo]);

  const selectedFeature = selectedId
    ? features.find((f) => f.properties.id === selectedId)
    : undefined;

  return (
    <div className={styles.container}>
      <div ref={containerRef} className={styles.map} />
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

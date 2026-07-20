import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import type { GeoJsonFeature } from "../../client/types.gen";
import { createMarkerElement } from "./markerElement";
import styles from "./MapView.module.css";

const MAPTILER_KEY = import.meta.env.VITE_MAPTILER_KEY as string | undefined;
const STYLE_URL = MAPTILER_KEY
  ? `https://api.maptiler.com/maps/streets-v2/style.json?key=${MAPTILER_KEY}`
  : "https://demotiles.maplibre.org/style.json";

const GREECE_CENTER: [number, number] = [23.7, 38.5];
const GREECE_ZOOM = 5.6;

interface MapViewProps {
  features: GeoJsonFeature[];
  onSelectEvent: (id: string) => void;
  selectedId?: string | null;
}

export function MapView({ features, onSelectEvent, selectedId }: MapViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markersRef = useRef<maplibregl.Marker[]>([]);
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
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "bottom-right");
    mapRef.current = map;
    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const attach = () => {
      markersRef.current.forEach((m) => m.remove());
      markersRef.current = features
        .filter((f) => f.geometry.coordinates.length === 2)
        .map((feature) => {
          const [lon, lat] = feature.geometry.coordinates;
          const el = createMarkerElement(
            feature.properties,
            feature.properties.article_count,
            feature.properties.id === selectedId,
          );
          el.addEventListener("click", () => onSelectEventRef.current(feature.properties.id));
          return new maplibregl.Marker({ element: el }).setLngLat([lon, lat]).addTo(map);
        });
    };

    if (map.isStyleLoaded()) attach();
    else map.once("load", attach);

    return () => {
      markersRef.current.forEach((m) => m.remove());
      markersRef.current = [];
    };
  }, [features, selectedId]);

  return (
    <div className={styles.container}>
      <div ref={containerRef} className={styles.map} />
    </div>
  );
}

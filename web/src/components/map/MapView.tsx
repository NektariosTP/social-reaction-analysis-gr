import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import type { GeoJsonFeature } from "../../client/types.gen";
import { intensityLevel } from "../../i18n";
import { INTENSITY_COLORS, INTENSITY_COLOR_NEUTRAL } from "./bubbleColors";
import styles from "./MapView.module.css";

const MAPTILER_KEY = import.meta.env.VITE_MAPTILER_KEY as string | undefined;
const STYLE_URL = MAPTILER_KEY
  ? `https://api.maptiler.com/maps/streets-v2/style.json?key=${MAPTILER_KEY}`
  : "https://demotiles.maplibre.org/style.json";

const GREECE_CENTER: [number, number] = [23.7, 38.5];
const GREECE_ZOOM = 5.6;

function bubbleSize(articleCount: number): number {
  return Math.min(64, Math.max(24, 16 + Math.sqrt(articleCount) * 10));
}

function bubbleColor(intensity: string | null | undefined): string {
  const level = intensityLevel(intensity);
  return level ? INTENSITY_COLORS[level] : INTENSITY_COLOR_NEUTRAL;
}

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
          const size = bubbleSize(feature.properties.article_count);
          const el = document.createElement("div");
          el.className = styles.bubble;
          el.style.width = `${size}px`;
          el.style.height = `${size}px`;
          el.style.fontSize = size > 40 ? "13px" : "11px";
          el.style.borderColor = bubbleColor(feature.properties.intensity);
          if (feature.properties.id === selectedId) {
            el.style.outline = "2px solid var(--color-accent)";
            el.style.outlineOffset = "2px";
          }
          el.textContent = String(feature.properties.article_count);
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

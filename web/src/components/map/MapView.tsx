import { useEffect, useRef, useState, type CSSProperties } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import type { GeoJsonFeature } from "../../client/types.gen";
import { useIsMobile } from "../../hooks/useIsMobile";
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
const GREECE_ZOOM_MOBILE = 5.6;
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
  /** Rendered height (px) of MapLegend — used to keep the fullscreen/zoom/attribution
   * controls (vertically centred on the right edge) clear of it on short viewports. */
  legendHeight?: number;
  /** Rendered height (px) of the pinned mobile header — used both to keep the
   * attribution control clear of it and to frame the initial map view. */
  headerHeight?: number;
  /** Mobile-only: combined height (px) of the bottom nav bar and the sheet's
   * peek height — used to keep the initial map view framed above them. */
  bottomInset?: number;
  showPopup?: boolean;
}

export function MapView({
  features,
  onSelectEvent,
  selectedId,
  flyTo,
  onReadMorePopup,
  onClosePopup,
  obstructedLeft = 0,
  legendHeight = 0,
  headerHeight = 0,
  bottomInset = 0,
  showPopup = true,
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
  const isMobile = useIsMobile();

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: STYLE_URL,
      center: GREECE_CENTER,
      zoom: isMobile ? GREECE_ZOOM_MOBILE : GREECE_ZOOM,
      minZoom: GREECE_MIN_ZOOM,
      // Attribution is added explicitly below, forced compact — the default (non-compact)
      // control can render as a wide inline text strip that overlaps MapLegend.
      attributionControl: false,
    });
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "bottom-right");
    const fullscreenTarget = document.getElementById("root") ?? undefined;
    map.addControl(
      new maplibregl.FullscreenControl({ container: fullscreenTarget }),
      "bottom-right",
    );
    map.addControl(new maplibregl.AttributionControl({ compact: true }), "bottom-right");
    // MapLibre's compact AttributionControl opens itself on mount (and can reopen itself
    // later, e.g. once real style/source data arrives) — trying to *detect* whether a
    // given DOM mutation was "us" (a click) vs "the library" was unreliable (a single
    // click produces two mutations: the library's own class change, then the native
    // <details> toggle a tick later — easy to misread the second as an unwanted
    // auto-reopen). Instead we own the open/closed state outright: `desiredOpen` is the
    // single source of truth, applyState() makes the DOM match it, the click handler
    // fully neutralizes the library's own toggle (capture-phase stopPropagation runs
    // before its listener on the summary, preventDefault stops the native toggle), and
    // the observer just resyncs the DOM to `desiredOpen` on any drift — idempotent, so
    // no causation-guessing needed.
    const attribCleanup = (() => {
      const attribEl = containerRef.current?.querySelector<HTMLDetailsElement>(".maplibregl-ctrl-attrib");
      if (!attribEl) return undefined;
      let desiredOpen = false;
      const applyState = () => {
        attribEl.classList.toggle("maplibregl-compact-show", desiredOpen);
        // A closed <details> force-hides its non-<summary> children via a
        // browser UA `!important` rule that no author style can override, so
        // the `open` attribute must track desiredOpen — the CSS class alone
        // only affects the compact button's padding/shape, not visibility.
        if (desiredOpen) {
          attribEl.setAttribute("open", "");
        } else {
          attribEl.removeAttribute("open");
        }
      };
      applyState();
      const handleClick = (e: MouseEvent) => {
        e.preventDefault();
        e.stopPropagation();
        desiredOpen = !desiredOpen;
        applyState();
      };
      attribEl.addEventListener("click", handleClick, { capture: true });
      const observer = new MutationObserver(() => {
        const domOpen = attribEl.classList.contains("maplibregl-compact-show");
        const domHasOpenAttr = attribEl.hasAttribute("open");
        if (domOpen !== desiredOpen || domHasOpenAttr !== desiredOpen) applyState();
      });
      observer.observe(attribEl, { attributes: true, attributeFilter: ["open", "class"] });
      return () => {
        observer.disconnect();
        attribEl.removeEventListener("click", handleClick, { capture: true });
      };
    })();
    mapRef.current = map;
    setMapInstance(map);
    map.once("load", () => setStyleLoaded(true));
    return () => {
      attribCleanup?.();
      map.remove();
      mapRef.current = null;
      setMapInstance(null);
      setStyleLoaded(false);
    };
  }, []);

  const overlay = useLocationOverlay(mapInstance, styleLoaded, onSelectEvent);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !isMobile || !styleLoaded) return;
    map.setPadding({ top: headerHeight + 16, bottom: bottomInset + 16, left: 0, right: 0 });
  }, [isMobile, styleLoaded, headerHeight, bottomInset]);

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
    // On mobile, selecting an event only expands its inline analysis — the map
    // stays put until the user explicitly taps "View on map" (driven by the
    // `flyTo` prop). Auto-framing on selection is desktop-only.
    if (isMobile) return;
    const feature = featuresRef.current.find((f) => f.properties.id === selectedId);
    if (!feature) return;
    const [lng, lat] = feature.geometry.coordinates as [number, number];
    map.flyTo({
      center: [lng, lat],
      zoom: Math.max(map.getZoom(), 11),
      offset: [obstructedLeft / 2, 0],
    });
  }, [selectedId, obstructedLeft, isMobile]);

  const selectedFeature = selectedId
    ? features.find((f) => f.properties.id === selectedId)
    : undefined;

  return (
    <div
      className={styles.container}
      style={
        {
          "--legend-height": `${legendHeight}px`,
          "--header-height": `${headerHeight}px`,
        } as CSSProperties
      }
    >
      <div ref={containerRef} className={styles.map} data-testid="map-canvas" />
      {showPopup && mapInstance && selectedId && selectedFeature && onClosePopup && (
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

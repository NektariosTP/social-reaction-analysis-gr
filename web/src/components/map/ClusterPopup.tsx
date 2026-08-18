import { useEffect, useMemo, useRef } from "react";
import { createPortal } from "react-dom";
import maplibregl from "maplibre-gl";
import { useTranslation } from "react-i18next";
import { useEvent } from "../../api/queries";
import { useLang } from "../../hooks/useLang";
import { AxisTag, IntensityDots, Spinner } from "../common";
import styles from "./ClusterPopup.module.css";

interface ClusterPopupProps {
  map: maplibregl.Map;
  eventId: string;
  coordinates: [number, number];
  onReadMore?: (id: string) => void;
  onClose: () => void;
}

export function ClusterPopup({ map, eventId, coordinates, onReadMore, onClose }: ClusterPopupProps) {
  const { t } = useTranslation();
  const [lang] = useLang();
  const { data: event, isLoading } = useEvent(eventId);
  const popupRef = useRef<maplibregl.Popup | null>(null);
  const container = useMemo(() => document.createElement("div"), []);

  useEffect(() => {
    const popup = new maplibregl.Popup({
      closeButton: false,
      closeOnClick: false,
      anchor: "bottom",
      offset: 20,
    })
      .setLngLat(coordinates)
      .setDOMContent(container)
      .addTo(map);
    popupRef.current = popup;
    return () => {
      popup.remove();
      popupRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [map, container]);

  useEffect(() => {
    popupRef.current?.setLngLat(coordinates);
  }, [coordinates]);

  return createPortal(
    <div className={styles.popup}>
      <button className={styles.closeBtn} onClick={onClose} aria-label="Close">
        ✕
      </button>
      {isLoading && <Spinner />}
      {event && (
        <>
          <div className={styles.tags}>
            {event.action_forms.map((v) => (
              <AxisTag key={v} value={v} variant="action" />
            ))}
            {event.thematic_fields.map((v) => (
              <AxisTag key={v} value={v} variant="theme" />
            ))}
            {event.channel && <AxisTag value={event.channel} variant="channel" />}
            <IntensityDots value={event.intensity} />
          </div>
          <div className={styles.headline}>
            {(lang === "el" ? event.summary_el : event.summary_en) ?? "…"}
          </div>
          <div className={styles.meta}>
            {event.source_count} {t("card.sources")}
          </div>
          {onReadMore && (
            <button className={styles.ctaBtn} onClick={() => onReadMore(event.id)}>
              {t("card.readMore")}
            </button>
          )}
        </>
      )}
    </div>,
    container,
  );
}

import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { ClusterDetailContent } from "./ClusterDetailContent";
import styles from "./InlineAnalysis.module.css";

interface InlineAnalysisProps {
  eventId: string;
  /** When provided, renders a "View on map" CTA that drops the sheet and frames
   * the event. Omitted on desktop (where the map is always visible). */
  onViewOnMap?: () => void;
}

/** The event's full analysis, expanded inline beneath its list card. Animates
 * open (grid-rows 0fr → 1fr) so the content grows in smoothly rather than
 * snapping the layout. */
export function InlineAnalysis({ eventId, onViewOnMap }: InlineAnalysisProps) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(false);

  // Start collapsed, then flip to open on the next frame so the grid-rows
  // transition actually runs (a value change, not an initial paint).
  useEffect(() => {
    const raf = requestAnimationFrame(() => setOpen(true));
    return () => cancelAnimationFrame(raf);
  }, []);

  return (
    <div className={styles.wrap} data-open={open || undefined} data-inline-detail={eventId}>
      <div className={styles.inner}>
        <ClusterDetailContent eventId={eventId} showHeadline={false} showMeta={false} flushTop />
        {onViewOnMap && (
          <div className={styles.ctaBar}>
            <button type="button" className={styles.viewOnMap} onClick={onViewOnMap}>
              <span aria-hidden="true">📍</span> {t("cluster.viewOnMap")}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useEvent } from "../../api/queries";
import { useLang } from "../../hooks/useLang";
import { formatRelativeTime } from "../../utils/time";
import { AxisTag, IntensityDots, Spinner, ErrorState } from "../common";
import styles from "./ClusterDetailPanel.module.css";

interface ClusterDetailPanelProps {
  eventId: string;
  onClose: () => void;
}

export function ClusterDetailPanel({ eventId, onClose }: ClusterDetailPanelProps) {
  const { t } = useTranslation();
  const [lang] = useLang();
  const { data: event, isLoading, isError } = useEvent(eventId);

  return (
    <div className={styles.panel}>
      <div className={styles.header}>
        <span>CLUSTER #{eventId.slice(0, 8)}</span>
        <button className={styles.closeBtn} onClick={onClose} aria-label="Close">
          ✕
        </button>
      </div>

      <div className={styles.body}>
        {isLoading && <Spinner />}
        {isError && <ErrorState />}
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

            <div className={styles.metaChips}>
              {event.region_code && <span className={styles.metaChip}>📍 {event.region_code}</span>}
              {event.first_seen && (
                <span className={styles.metaChip}>🕑 {formatRelativeTime(event.first_seen, lang)}</span>
              )}
              <span className={styles.metaChip}>
                {event.source_count} {t("card.sources")}
              </span>
            </div>

            <div className={styles.sectionLabel}>{t("cluster.narrative")}</div>
            <p className={styles.summary}>
              {(lang === "el" ? event.summary_el : event.summary_en) ?? "—"}
            </p>

            <div className={styles.sectionLabel}>
              {t("cluster.sourceEvidence")} ({event.articles?.length ?? 0})
            </div>
            {event.articles?.slice(0, 3).map((a) => (
              <div className={styles.sourceRow} key={a.id}>
                <span>{a.source_id ?? a.title ?? a.url}</span>
                <span>{formatRelativeTime(a.published_at, lang)}</span>
              </div>
            ))}

            <Link to={`/cluster/${event.id}`} className={styles.ctaBtn}>
              {t("card.viewFullAnalysis")}
            </Link>
          </>
        )}
      </div>
    </div>
  );
}

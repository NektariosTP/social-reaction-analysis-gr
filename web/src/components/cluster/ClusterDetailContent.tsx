import { useTranslation } from "react-i18next";
import { useEvent } from "../../api/queries";
import { useLang } from "../../hooks/useLang";
import { regionLabel } from "../../i18n/regions";
import { formatRelativeTime } from "../../utils/time";
import { AxisTag, IntensityDots, Spinner, ErrorState } from "../common";
import { EventContextPanel } from "../context/EventContextPanel";
import { ClassificationTable } from "./ClassificationTable";
import { SourceEvidenceList } from "./SourceEvidenceList";
import { SourceBreakdown } from "./SourceBreakdown";
import { ClusterTimeline } from "./ClusterTimeline";
import { OfficialStatements } from "./OfficialStatements";
import { RelatedClusters } from "./RelatedClusters";
import styles from "./ClusterDetailContent.module.css";

interface ClusterDetailContentProps {
  eventId: string;
}

export function ClusterDetailContent({ eventId }: ClusterDetailContentProps) {
  const { t } = useTranslation();
  const [lang] = useLang();
  const { data: event, isLoading, isError } = useEvent(eventId);

  if (isLoading) return <Spinner />;
  if (isError) return <ErrorState />;
  if (!event) return null;

  return (
    <div className={styles.content}>
      <div className={styles.tags}>
        {event.action_forms.map((v) => (
          <AxisTag key={v} value={v} variant="action" />
        ))}
        {event.thematic_fields.map((v) => (
          <AxisTag key={v} value={v} variant="theme" />
        ))}
        {event.channel && <AxisTag value={event.channel} variant="channel" />}
        <IntensityDots value={event.intensity} showLabel />
      </div>

      <h2 className={styles.headline}>{(lang === "el" ? event.summary_el : event.summary_en) ?? "…"}</h2>

      <div className={styles.metaChips}>
        {event.region_code && <span className={styles.metaChip}>📍 {regionLabel(event.region_code, lang)}</span>}
        <span className={styles.metaChip}>
          {event.article_count} {t("card.sources")}
        </span>
        {event.first_seen && (
          <span className={styles.metaChip}>{formatRelativeTime(event.first_seen, lang)}</span>
        )}
      </div>

      <div className={styles.section}>
        <div className={styles.sectionLabel}>{t("cluster.narrative")}</div>
        <p className={styles.narrative}>{(lang === "el" ? event.summary_el : event.summary_en) ?? "—"}</p>
      </div>

      <div className={styles.section}>
        <ClusterTimeline />
      </div>

      <div className={styles.section}>
        <div className={styles.sectionLabel}>
          {t("cluster.sourceEvidence")} ({event.articles?.length ?? 0})
        </div>
        <SourceEvidenceList articles={event.articles ?? []} />
      </div>

      <div className={styles.section}>
        <OfficialStatements />
      </div>

      <div className={styles.section}>
        <div className={styles.sectionLabel}>{t("cluster.classification")}</div>
        <ClassificationTable event={event} />
      </div>

      <div className={styles.section}>
        <div className={styles.sectionLabel}>{t("cluster.sourceBreakdown")}</div>
        <SourceBreakdown articles={event.articles ?? []} />
      </div>

      <div className={styles.section}>
        <RelatedClusters />
      </div>

      <EventContextPanel eventId={event.id} />
    </div>
  );
}

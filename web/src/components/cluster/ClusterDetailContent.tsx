import { useTranslation } from "react-i18next";
import { useEvent } from "../../api/queries";
import { useLang } from "../../hooks/useLang";
import { formatRelativeTime } from "../../utils/time";
import { AxisTag, Spinner, ErrorState } from "../common";
import { ClassificationTable } from "./ClassificationTable";
import { SourceEvidenceList } from "./SourceEvidenceList";
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
        {event.intensity && <AxisTag value={event.intensity} variant="intensity" />}
      </div>

      <h2 className={styles.headline}>{(lang === "el" ? event.summary_el : event.summary_en) ?? "…"}</h2>

      <div className={styles.metaChips}>
        <span className={styles.metaChip}>
          {event.article_count} {t("card.sources")}
        </span>
        {event.first_seen && (
          <span className={styles.metaChip}>{formatRelativeTime(event.first_seen, lang)}</span>
        )}
      </div>

      <div className={styles.section}>
        <div className={styles.sectionLabel}>{t("cluster.classification")}</div>
        <ClassificationTable event={event} />
      </div>

      <div className={styles.section}>
        <div className={styles.sectionLabel}>
          {t("cluster.sourceEvidence")} ({event.articles?.length ?? 0})
        </div>
        <SourceEvidenceList articles={event.articles ?? []} />
      </div>
    </div>
  );
}

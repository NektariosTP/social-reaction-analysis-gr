import { useTranslation } from "react-i18next";
import { useEvent } from "../../api/queries";
import { useLang } from "../../hooks/useLang";
import { formatRelativeTime } from "../../utils/time";
import { sourceCountDisplay } from "../../utils/sourceDisplay";
import { Spinner, ErrorState } from "../common";
import { ClassificationTable } from "./ClassificationTable";
import { SourceEvidenceList } from "./SourceEvidenceList";
import { UnionSourceList } from "./UnionSourceList";
import styles from "./ClusterDetailContent.module.css";

interface ClusterDetailContentProps {
  eventId: string;
  showHeadline?: boolean;
  /** The article-count / first-seen meta chips. Hidden in the mobile inline
   * analysis, where the story card above already shows the same numbers. */
  showMeta?: boolean;
  /** Drops the top border of the first section — used in the mobile inline
   * analysis so it doesn't double up with the panel's own top border. */
  flushTop?: boolean;
}

export function ClusterDetailContent({
  eventId,
  showHeadline = true,
  showMeta = true,
  flushTop = false,
}: ClusterDetailContentProps) {
  const { t } = useTranslation();
  const [lang] = useLang();
  const { data: event, isLoading, isError } = useEvent(eventId);

  if (isLoading) return <Spinner />;
  if (isError) return <ErrorState />;
  if (!event) return null;

  return (
    <div className={`${styles.content} ${flushTop ? styles.flushTop : ""}`}>
      {showHeadline && (
        <h2 className={styles.headline}>{(lang === "el" ? event.summary_el : event.summary_en) ?? "…"}</h2>
      )}

      {showMeta && (
        <div className={styles.metaChips}>
          <span className={styles.metaChip}>
            {sourceCountDisplay(event).count} {t(sourceCountDisplay(event).labelKey)}
          </span>
          {event.first_seen && (
            <span className={styles.metaChip}>{formatRelativeTime(event.first_seen, lang)}</span>
          )}
        </div>
      )}

      <div className={styles.section}>
        <div className={styles.sectionLabel}>{t("cluster.classification")}</div>
        <ClassificationTable event={event} />
      </div>

      {event.reactions && event.reactions.length > 0 && (
        <div className={styles.section}>
          <div className={styles.sectionLabel}>
            {t("cluster.unions")} ({event.reactions.length})
          </div>
          <UnionSourceList reactions={event.reactions} />
        </div>
      )}

      <div className={styles.section}>
        <div className={styles.sectionLabel}>
          {t("cluster.sourceEvidence")} ({event.articles?.length ?? 0})
        </div>
        <SourceEvidenceList articles={event.articles ?? []} />
      </div>
    </div>
  );
}

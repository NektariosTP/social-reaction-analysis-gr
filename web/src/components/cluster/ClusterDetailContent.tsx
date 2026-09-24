import { useTranslation } from "react-i18next";
import { useEvent } from "../../api/queries";
import { useLang } from "../../hooks/useLang";
import { sourceCountDisplay } from "../../utils/sourceDisplay";
import { dedupeUnions } from "../../utils/unionDedup";
import { Spinner, ErrorState, TemporalBanner } from "../common";
import { ClassificationTable } from "./ClassificationTable";
import { SourceEvidenceList } from "./SourceEvidenceList";
import { UnionSourceList } from "./UnionSourceList";
import styles from "./ClusterDetailContent.module.css";

interface ClusterDetailContentProps {
  eventId: string;
  showHeadline?: boolean;
  /** The article-count meta chip. Hidden in the mobile inline analysis, where
   * the story card above already shows the same number. */
  showMeta?: boolean;
  /** Drops the top border of the first section — used in the mobile inline
   * analysis so it doesn't double up with the panel's own top border. */
  flushTop?: boolean;
  /** The highlighted time/unions banner. Hidden in the mobile inline analysis,
   * where the story card above already shows it. */
  showBanner?: boolean;
}

export function ClusterDetailContent({
  eventId,
  showHeadline = true,
  showMeta = true,
  showBanner = true,
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

      {showBanner && <TemporalBanner event={event} />}

      {showMeta && (
        <div className={styles.metaChips}>
          <span className={styles.metaChip}>
            {sourceCountDisplay(event).count} {t(sourceCountDisplay(event).labelKey)}
          </span>
        </div>
      )}

      <div className={styles.section}>
        <div className={styles.sectionLabel}>{t("cluster.classification")}</div>
        <ClassificationTable event={event} />
      </div>

      {event.reactions && event.reactions.length > 0 && (
        <div className={styles.section}>
          <div className={styles.sectionLabel}>
            {t("cluster.unions")} ({dedupeUnions(event.reactions).length})
          </div>
          <UnionSourceList reactions={event.reactions} />
        </div>
      )}

      <div className={styles.section}>
        <div className={styles.sectionLabel}>
          {/* source_count is the authoritative total (all non-duplicate articles +
              reactions), same value the badge shows. The articles array can be
              capped for very large events, so never count it here. */}
          {t("cluster.sourceEvidence")} ({event.source_count})
        </div>
        <SourceEvidenceList articles={event.articles ?? []} reactions={event.reactions ?? []} />
      </div>
    </div>
  );
}

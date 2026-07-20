import { useTranslation } from "react-i18next";
import { useEvent } from "../../api/queries";
import { useLang } from "../../hooks/useLang";
import { formatRelativeTime } from "../../utils/time";
import { MapView } from "../map";
import { AxisTag, IntensityDots, Spinner, ErrorState } from "../common";
import { ClassificationTable } from "./ClassificationTable";
import { SourceEvidenceList } from "./SourceEvidenceList";
import { SourceBreakdown } from "./SourceBreakdown";
import { ClusterTimeline } from "./ClusterTimeline";
import { OfficialStatements } from "./OfficialStatements";
import { RelatedClusters } from "./RelatedClusters";
import type { GeoJsonFeature } from "../../client/types.gen";
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

  const miniMapFeature: GeoJsonFeature[] =
    event.lat != null && event.lon != null
      ? [
          {
            geometry: { coordinates: [event.lon, event.lat] },
            properties: {
              id: event.id,
              action_forms: event.action_forms,
              thematic_fields: event.thematic_fields,
              channel: event.channel,
              intensity: event.intensity,
              summary_en: event.summary_en,
              article_count: event.article_count,
              first_seen: event.first_seen,
            },
          },
        ]
      : [];

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
        {event.region_code && <span className={styles.metaChip}>📍 {event.region_code}</span>}
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

      {miniMapFeature.length > 0 && (
        <div className={styles.miniMap}>
          <MapView features={miniMapFeature} onSelectEvent={() => {}} />
        </div>
      )}

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
    </div>
  );
}

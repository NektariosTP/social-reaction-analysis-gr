import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useEvent } from "../api/queries";
import { useLang } from "../hooks/useLang";
import { formatRelativeTime } from "../utils/time";
import { AppShell } from "../components/layout";
import { MapView } from "../components/map";
import { AxisTag, IntensityDots, Spinner, ErrorState } from "../components/common";
import {
  ClassificationTable,
  SourceEvidenceList,
  SourceBreakdown,
  ClusterTimeline,
  OfficialStatements,
  RelatedClusters,
} from "../components/cluster";
import type { GeoJsonFeature } from "../client/types.gen";
import styles from "./ClusterPage.module.css";

export function ClusterPage() {
  const { id } = useParams<{ id: string }>();
  const { t } = useTranslation();
  const [lang] = useLang();
  const { data: event, isLoading, isError } = useEvent(id);
  const [cited, setCited] = useState(false);

  const exportJson = () => {
    if (!event) return;
    const blob = new Blob([JSON.stringify(event, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `reaction-map-cluster-${event.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const cite = () => {
    if (!event) return;
    const citation = `Reaction Map, cluster #${event.id}, retrieved ${new Date().toISOString().slice(0, 10)}, ${window.location.href}`;
    void navigator.clipboard.writeText(citation);
    setCited(true);
    setTimeout(() => setCited(false), 2000);
  };

  const miniMapFeature: GeoJsonFeature[] =
    event?.lat != null && event?.lon != null
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
    <AppShell>
      <div className={styles.navBar}>
        <div className={styles.crumbs}>
          <Link to="/">‹ {t("nav.backToMap")}</Link>
          <span>/</span>
          <span>Cluster #{id?.slice(0, 8)}</span>
        </div>
        <div className={styles.actions}>
          <button className={styles.actionBtn} onClick={cite} disabled={!event}>
            📋 {cited ? "Copied!" : t("cluster.cite")}
          </button>
          <button className={styles.actionBtn} onClick={exportJson} disabled={!event}>
            ⬇ {t("cluster.export")}
          </button>
        </div>
      </div>

      {isLoading && <Spinner />}
      {isError && <ErrorState />}

      {event && (
        <>
          <div className={styles.header}>
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
            <h1 className={styles.headline}>
              {(lang === "el" ? event.summary_el : event.summary_en) ?? "…"}
            </h1>
            <div className={styles.metaChips}>
              {event.region_code && <span className={styles.metaChip}>📍 {event.region_code}</span>}
              <span className={styles.metaChip}>
                {event.article_count} {t("card.sources")}
              </span>
              <span className={styles.metaChip}>{event.source_count} distinct outlets</span>
              {event.first_seen && (
                <span className={styles.metaChip}>
                  First detected {formatRelativeTime(event.first_seen, lang)}
                </span>
              )}
              {event.last_seen && (
                <span className={styles.metaChip}>Updated {formatRelativeTime(event.last_seen, lang)}</span>
              )}
            </div>
          </div>

          <div className={styles.body}>
            <div className={styles.main}>
              <div className={styles.section}>
                <div className={styles.sectionLabel}>{t("cluster.narrative")}</div>
                <p className={styles.narrative}>
                  {(lang === "el" ? event.summary_el : event.summary_en) ?? "—"}
                </p>
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
            </div>

            <div className={styles.sidebar}>
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
          </div>
        </>
      )}
    </AppShell>
  );
}

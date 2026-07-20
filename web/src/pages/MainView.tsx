import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useEvents, useEventsGeoJSON, useRecentEventsCount, applyClientFilters } from "../api/queries";
import { useFilterState, timeRangeToDateFrom } from "../hooks/useFilterState";
import { useLang } from "../hooks/useLang";
import { useOnboardingSeen } from "../hooks/useOnboardingSeen";
import { Footer } from "../components/layout";
import { MapView, MapLegend } from "../components/map";
import { StoryCard } from "../components/cards";
import { ClusterDetailPanel } from "../components/cluster";
import { OnboardingOverlay } from "../components/onboarding";
import { Spinner, ErrorState, EmptyState } from "../components/common";
import styles from "./MainView.module.css";

export function MainView() {
  const { t } = useTranslation();
  const [lang] = useLang();
  const { seen, dismiss } = useOnboardingSeen();
  const { filters } = useFilterState();

  const [searchQuery, setSearchQuery] = useState("");
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);

  const dateFrom = timeRangeToDateFrom(filters.timeRange);
  const eventsQuery = useEvents({
    actionForms: filters.actionForms,
    thematicFields: filters.thematicFields,
    channel: filters.channel ?? undefined,
    intensities: filters.intensities,
    dateFrom,
    limit: 100,
  });
  const geojsonQuery = useEventsGeoJSON({ channel: filters.channel ?? undefined });
  const recentCountQuery = useRecentEventsCount();

  const events = eventsQuery.data ?? [];
  const q = searchQuery.trim().toLowerCase();
  const filteredEvents = q
    ? events.filter((e) => (lang === "el" ? e.summary_el : e.summary_en)?.toLowerCase().includes(q))
    : events;

  const geoFeatures = applyClientFilters(
    (geojsonQuery.data?.features ?? []).map((f) => ({ ...f.properties, feature: f })),
    filters,
  ).map((p) => p.feature);

  const locationKey = (e: (typeof events)[number]) =>
    e.region_code ?? (e.lat != null && e.lon != null ? `${e.lat.toFixed(2)},${e.lon.toFixed(2)}` : null);
  const locationsCount = new Set(events.map(locationKey).filter(Boolean)).size;

  return (
    <div className={styles.page}>
      <div className={styles.mapLayer}>
        {geojsonQuery.isLoading ? (
          <Spinner />
        ) : geojsonQuery.isError ? (
          <ErrorState />
        ) : (
          <MapView features={geoFeatures} onSelectEvent={setSelectedEventId} selectedId={selectedEventId} />
        )}
        <MapLegend />
        {selectedEventId && (
          <ClusterDetailPanel eventId={selectedEventId} onClose={() => setSelectedEventId(null)} />
        )}
      </div>

      <div className={styles.blocks}>
        <div className={styles.headerBlock}>
          <div className={styles.brandRow}>
            <span className={styles.mark}>R</span>
            <span className={styles.brandName}>{t("brand")}</span>
            <span className={styles.live}>● {t("live")}</span>
          </div>
          <div className={styles.searchRow}>
            <input
              className={styles.searchInput}
              placeholder={t("search.placeholder")}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        </div>

        <div className={styles.editorialBlock}>
          <div className={styles.kpiStrip}>
            <div className={styles.kpiCell}>
              <div className={styles.kpiValue}>{eventsQuery.isLoading ? "—" : filteredEvents.length}</div>
              <div className={styles.kpiLabel}>{t("kpi.active")}</div>
            </div>
            <div className={styles.kpiCell}>
              <div className={styles.kpiValue}>{locationsCount}</div>
              <div className={styles.kpiLabel}>{t("kpi.locations")}</div>
            </div>
            <div className={styles.kpiCell}>
              <div className={styles.kpiValue}>+{recentCountQuery.data ?? "—"}</div>
              <div className={styles.kpiLabel}>{t("kpi.newLastHour")}</div>
            </div>
          </div>
          <div className={styles.feedHeader}>
            <span>{t("feed.title")}</span>
            <span>
              {t("feed.nlpClustered")} · {filteredEvents.length}
            </span>
          </div>
          <div className={styles.feedList}>
            {eventsQuery.isLoading && <Spinner />}
            {eventsQuery.isError && <ErrorState />}
            {!eventsQuery.isLoading && !eventsQuery.isError && filteredEvents.length === 0 && (
              <EmptyState />
            )}
            {filteredEvents.map((e, i) => (
              <StoryCard key={e.id} event={e} variant={i === 0 ? "featured" : "compact"} />
            ))}
          </div>
        </div>
      </div>

      <div className={styles.footerBar}>
        <Footer />
      </div>

      {!seen && <OnboardingOverlay onDismiss={dismiss} />}
    </div>
  );
}

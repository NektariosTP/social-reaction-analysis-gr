import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useEvents, useEventsGeoJSON, useRecentEventsCount } from "../api/queries";
import { applyClientFilters } from "../api/queries";
import { useFilterState, timeRangeToDateFrom } from "../hooks/useFilterState";
import { useLang } from "../hooks/useLang";
import { useOnboardingSeen } from "../hooks/useOnboardingSeen";
import { TopBar, Footer } from "../components/layout";
import { MapView, MapLegend } from "../components/map";
import { FilterPanel } from "../components/filters";
import { StoryCard } from "../components/cards";
import { ClusterDetailPanel } from "../components/cluster";
import { OnboardingOverlay } from "../components/onboarding";
import { Spinner, ErrorState, EmptyState } from "../components/common";
import styles from "./MainView.module.css";

type ViewMode = "split" | "immersive";

export function MainView() {
  const { t } = useTranslation();
  const [lang] = useLang();
  const { seen, dismiss } = useOnboardingSeen();
  const { filters, setFilters, toggleInList } = useFilterState();

  const [viewMode, setViewMode] = useState<ViewMode>("split");
  const [filterOpen, setFilterOpen] = useState(false);
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

  // region_code isn't populated for every event yet (geocoding pipeline gap) —
  // fall back to rounded coordinates so the KPI reflects real geocoded spread
  // rather than reporting zero whenever region_code is null.
  const locationKey = (e: (typeof events)[number]) =>
    e.region_code ?? (e.lat != null && e.lon != null ? `${e.lat.toFixed(2)},${e.lon.toFixed(2)}` : null);
  const locationsCount = new Set(events.map(locationKey).filter(Boolean)).size;

  const kpiStrip = (
    <>
      <div>
        <b>{eventsQuery.isLoading ? "—" : filteredEvents.length}</b> {t("kpi.active")}
      </div>
      <div>
        <b>{locationsCount}</b> {t("kpi.locations")}
      </div>
      <div>
        +<b>{recentCountQuery.data ?? "—"}</b> {t("kpi.newLastHour")}
      </div>
    </>
  );

  const searchInput = (
    <input
      className={styles.searchInput}
      style={viewMode === "immersive" ? { width: "100%" } : undefined}
      placeholder={t("search.placeholder")}
      value={searchQuery}
      onChange={(e) => setSearchQuery(e.target.value)}
    />
  );

  if (viewMode === "immersive") {
    return (
      <div className={styles.immersive}>
        {geojsonQuery.isLoading ? (
          <Spinner />
        ) : geojsonQuery.isError ? (
          <ErrorState />
        ) : (
          <MapView features={geoFeatures} onSelectEvent={setSelectedEventId} selectedId={selectedEventId} />
        )}
        <button className={styles.floatingBackBtn} onClick={() => setViewMode("split")}>
          ⊞ {t("view.split")}
        </button>
        <div className={styles.floatingTop}>{searchInput}</div>
        <div className={styles.floatingFeed}>
          {filteredEvents.slice(0, 5).map((e) => (
            <StoryCard key={e.id} event={e} variant="compact" />
          ))}
        </div>
        <div className={styles.floatingKpi}>{kpiStrip}</div>
        <MapLegend />
        {selectedEventId && (
          <ClusterDetailPanel eventId={selectedEventId} onClose={() => setSelectedEventId(null)} />
        )}
        {!seen && <OnboardingOverlay onDismiss={dismiss} />}
      </div>
    );
  }

  return (
    <div className={styles.page}>
      <TopBar />
      <div className={styles.viewTabs}>
        <button className={`${styles.viewTab} ${styles.viewTabActive}`}>{t("view.split")}</button>
        <button className={styles.viewTab} onClick={() => setViewMode("immersive")}>
          {t("view.immersive")}
        </button>
      </div>
      <div className={styles.searchRow}>
        {searchInput}
        <button className={styles.filterToggle} onClick={() => setFilterOpen((o) => !o)}>
          {filterOpen ? "⋀" : "⋁"} {t("filters.title")}
        </button>
      </div>
      {filterOpen && (
        <FilterPanel filters={filters} onToggle={toggleInList} onSetFilters={setFilters} />
      )}
      <div className={styles.split}>
        <div className={styles.mapPane}>
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
        <div className={styles.editorialPane}>
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
      <Footer />
      {!seen && <OnboardingOverlay onDismiss={dismiss} />}
    </div>
  );
}

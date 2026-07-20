import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useEvents, useEventsGeoJSON, useRecentEventsCount, applyClientFilters } from "../api/queries";
import { useFilterState, timeRangeToDateFrom } from "../hooks/useFilterState";
import { useLang } from "../hooks/useLang";
import { useOnboardingSeen } from "../hooks/useOnboardingSeen";
import { Footer } from "../components/layout";
import { MapView, MapLegend } from "../components/map";
import { ClusterDetailPanel } from "../components/cluster";
import { OnboardingOverlay } from "../components/onboarding";
import { HeaderBlock, EditorialBlock } from "../components/shell";
import { Spinner, ErrorState } from "../components/common";
import type { Region } from "../i18n/regions";
import styles from "./MainView.module.css";

export function MainView() {
  const [lang] = useLang();
  const { seen, dismiss } = useOnboardingSeen();
  const { filters, setFilters, toggleInList } = useFilterState();

  const [searchQuery, setSearchQuery] = useState("");
  const [flyTo, setFlyTo] = useState<{ center: [number, number]; zoom?: number } | null>(null);

  const { id: routeClusterId } = useParams<{ id?: string }>();
  const navigate = useNavigate();
  const [previewId, setPreviewId] = useState<string | null>(null);

  const mode: "list" | "detail" = routeClusterId ? "detail" : "list";
  const mapSelectedId = previewId ?? routeClusterId ?? null;

  function handleSelectEventFromMap(id: string) {
    if (mode === "detail") navigate(`/cluster/${id}`);
    else setPreviewId(id);
  }
  function handleReadMore(id: string) {
    setPreviewId(null);
    navigate(`/cluster/${id}`);
  }
  function handleClosePreview() {
    setPreviewId(null);
  }
  function handleSelectEventFromList(id: string) {
    setPreviewId(null);
    navigate(`/cluster/${id}`);
  }
  function handleBack() {
    navigate("/");
  }

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
          <MapView
            features={geoFeatures}
            onSelectEvent={handleSelectEventFromMap}
            selectedId={mapSelectedId}
            flyTo={flyTo}
          />
        )}
        <MapLegend />
        {mode === "list" && previewId && (
          <ClusterDetailPanel eventId={previewId} onClose={handleClosePreview} onReadMore={handleReadMore} />
        )}
      </div>

      <div className={styles.blocks}>
        <HeaderBlock
          searchQuery={searchQuery}
          onSearchChange={setSearchQuery}
          onSelectRegion={(region: Region) => setFlyTo({ center: region.center, zoom: 8 })}
          filters={filters}
          onToggleFilterValue={toggleInList}
          onSetFilters={setFilters}
        />

        <div className={styles.editorialBlock}>
          <EditorialBlock
            mode={mode}
            kpi={{
              active: eventsQuery.isLoading ? "—" : filteredEvents.length,
              locations: locationsCount,
              newLastHour: recentCountQuery.data ?? "—",
            }}
            events={filteredEvents}
            eventsLoading={eventsQuery.isLoading}
            eventsError={eventsQuery.isError}
            highlightedEventId={previewId}
            onSelectEvent={handleSelectEventFromList}
            detailEventId={routeClusterId ?? ""}
            onBack={handleBack}
          />
        </div>
      </div>

      <div className={styles.footerBar}>
        <Footer />
      </div>

      {!seen && <OnboardingOverlay onDismiss={dismiss} />}
    </div>
  );
}

import { useState } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import { useEvents, useEventsGeoJSON, useRecentEventsCount, useOngoingEvents, useUpcomingEvents, applyClientFilters } from "../api/queries";
import { useFilterState, timeRangeToDateFrom } from "../hooks/useFilterState";
import { useGeoView } from "../hooks/useGeoView";
import { useLang } from "../hooks/useLang";
import { useOnboardingSeen } from "../hooks/useOnboardingSeen";
import { Footer } from "../components/layout";
import { MapView, MapLegend } from "../components/map";
import { OnboardingOverlay } from "../components/onboarding";
import { HeaderBlock, EditorialBlock, TemporalBlock, UserControls, AreaBlock } from "../components/shell";
import { Spinner, ErrorState } from "../components/common";
import type { Region } from "../i18n/regions";
import styles from "./MainView.module.css";

export function MainView() {
  const [lang] = useLang();
  const { seen, dismiss } = useOnboardingSeen();
  const { filters, setFilters, toggleInList } = useFilterState();
  const [searchParams] = useSearchParams();
  const geo = useGeoView();

  const [searchQuery, setSearchQuery] = useState("");
  const [flyTo, setFlyTo] = useState<{ center: [number, number]; zoom?: number } | null>(null);

  const { id: routeClusterId } = useParams<{ id?: string }>();
  const navigate = useNavigate();
  const [previewId, setPreviewId] = useState<string | null>(null);

  const mode: "list" | "detail" = routeClusterId ? "detail" : "list";
  const mapSelectedId = previewId ?? routeClusterId ?? null;

  function handleSelectEventFromMap(id: string) {
    if (mode === "detail") navigate(`/cluster/${id}?${searchParams.toString()}`);
    else setPreviewId(id);
  }
  function handleReadMore(id: string) {
    setPreviewId(null);
    navigate(`/cluster/${id}?${searchParams.toString()}`);
  }
  function handleClosePreview() {
    setPreviewId(null);
  }
  function handleClosePopup() {
    if (mode === "detail") handleBack();
    else handleClosePreview();
  }
  function handleSelectEventFromList(id: string) {
    setPreviewId(null);
    navigate(`/cluster/${id}?${searchParams.toString()}`);
  }
  function handleBack() {
    navigate(`/?${searchParams.toString()}`);
  }

  const dateFrom = timeRangeToDateFrom(filters.timeRange);
  const eventsQuery = useEvents({
    actionForms: filters.actionForms,
    thematicFields: filters.thematicFields,
    channel: filters.channel ?? undefined,
    intensities: filters.intensities,
    dateFrom,
    limit: 100,
    regionCode: geo.region ?? undefined,
    municipality: geo.municipality ?? undefined,
  });
  const geojsonQuery = useEventsGeoJSON({ channel: filters.channel ?? undefined });
  const recentCountQuery = useRecentEventsCount();
  const ongoingQuery = useOngoingEvents();
  const upcomingQuery = useUpcomingEvents();

  const events = eventsQuery.data ?? [];
  const q = searchQuery.trim().toLowerCase();
  const filteredEvents = q
    ? events.filter((e) => (lang === "el" ? e.summary_el : e.summary_en)?.toLowerCase().includes(q))
    : events;

  const geoFeatures = applyClientFilters(
    (geojsonQuery.data?.features ?? []).map((f) => ({ ...f.properties, feature: f })),
    { ...filters, regionCode: geo.region ?? undefined, municipality: geo.municipality ?? undefined },
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
            onReadMorePopup={mode === "list" ? handleReadMore : undefined}
            onClosePopup={handleClosePopup}
            geoView={geo}
            onSelectPeriphery={geo.selectPeriphery}
            onSelectMunicipality={geo.selectMunicipality}
          />
        )}
        <MapLegend />
      </div>

      <div className={styles.blocks}>
        <div className={styles.headerBlock}>
          <HeaderBlock
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            onSelectRegion={(region: Region) => setFlyTo({ center: region.center, zoom: 8 })}
            filters={filters}
            onToggleFilterValue={toggleInList}
            onSetFilters={setFilters}
          />
        </div>

        <div className={styles.scrollColumn}>
          {mode === "list" && (
            <TemporalBlock
              ongoing={ongoingQuery.data ?? []}
              upcoming={upcomingQuery.data ?? []}
              loading={ongoingQuery.isLoading || upcomingQuery.isLoading}
              error={ongoingQuery.isError || upcomingQuery.isError}
              onSelectEvent={handleSelectEventFromList}
            />
          )}

          {geo.level !== "none" && (
            <AreaBlock
              title={geo.level === "municipality" ? `${geo.municipality} — ${geo.region}` : geo.region!}
              events={filteredEvents}
              loading={eventsQuery.isLoading}
              onClose={geo.level === "municipality" ? geo.clearMunicipality : geo.clear}
            />
          )}

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
      </div>

      <div className={styles.footerBar}>
        <Footer />
      </div>

      <div className={styles.topRightControls}>
        <UserControls />
      </div>

      {!seen && <OnboardingOverlay onDismiss={dismiss} />}
    </div>
  );
}

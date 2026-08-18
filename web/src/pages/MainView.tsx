import { useEffect, useRef, useState } from "react";
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
import { regionLabel } from "../i18n/regions";
import styles from "./MainView.module.css";

export function MainView() {
  const [lang] = useLang();
  const { seen, dismiss } = useOnboardingSeen();
  const { filters, setFilters, toggleInList } = useFilterState();
  const [searchParams] = useSearchParams();
  const geo = useGeoView();

  const [searchQuery, setSearchQuery] = useState("");
  const [flyTo, setFlyTo] = useState<{ center: [number, number]; zoom?: number } | null>(null);

  // The floating sidebar (.blocks) sits on top of the map and its width is
  // responsive (clamp(360px, 28vw, 480px) — see MainView.module.css), so map
  // framing (fitBounds/flyTo) needs to know its real rendered width to avoid
  // centering selected content underneath it.
  const sidebarRef = useRef<HTMLDivElement>(null);
  const [sidebarWidth, setSidebarWidth] = useState(0);
  useEffect(() => {
    const el = sidebarRef.current;
    if (!el || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(([entry]) => setSidebarWidth(entry.contentRect.width));
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

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
  // Geo scoping (region/municipality) is done client-side, NOT via the API:
  // the server matches region_code exactly, but that column is language-
  // inconsistent in the data ("Αττική" vs "Attica"), so a server-side region
  // filter silently drops the Greek-coded events. applyClientFilters
  // canonicalises the region, matching how the map (geoFeatures) already scopes.
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
  const ongoingQuery = useOngoingEvents();
  const upcomingQuery = useUpcomingEvents();

  const events = applyClientFilters(eventsQuery.data ?? [], {
    regionCode: geo.region ?? undefined,
    municipality: geo.municipality ?? undefined,
  });
  const q = searchQuery.trim().toLowerCase();
  const filteredEvents = q
    ? events.filter((e) => (lang === "el" ? e.summary_el : e.summary_en)?.toLowerCase().includes(q))
    : events;

  const geoFeatures = applyClientFilters(
    (geojsonQuery.data?.features ?? []).map((f) => ({ ...f.properties, feature: f })),
    { ...filters, regionCode: geo.region ?? undefined, municipality: geo.municipality ?? undefined },
  ).map((p) => p.feature);

  // Count distinct plotted points, not region_code: the map pins each event at
  // its own lat/lon, so two events in the same periphery but different places
  // (e.g. Νάξος + Κως, both "South Aegean") are two locations, and region_code
  // is also language-inconsistent across events ("Αττική" vs "Attica"). Keying
  // on coordinates keeps the KPI consistent with what's on the map. Rounded to
  // ~110m so identical geocodes (e.g. venueless national events) still merge.
  const locationKey = (e: (typeof events)[number]) =>
    e.lat != null && e.lon != null ? `${e.lat.toFixed(3)},${e.lon.toFixed(3)}` : e.region_code ?? null;
  const locationsCount = new Set(filteredEvents.map(locationKey).filter(Boolean)).size;

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
            obstructedLeft={sidebarWidth}
          />
        )}
        <MapLegend />
      </div>

      <div className={styles.blocks} ref={sidebarRef}>
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
              title={
                geo.level === "municipality"
                  ? `${geo.municipality} — ${regionLabel(geo.region!, lang)}`
                  : regionLabel(geo.region!, lang)
              }
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

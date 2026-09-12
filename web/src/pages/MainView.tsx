import { useEffect, useRef, useState } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import { useEvents, useEventsGeoJSON, useOngoingEvents, useUpcomingEvents, applyClientFilters } from "../api/queries";
import { useFilterState, timeRangeToDateFrom } from "../hooks/useFilterState";
import { useLang } from "../hooks/useLang";
import { useOnboardingSeen } from "../hooks/useOnboardingSeen";
import { Footer } from "../components/layout";
import { MapView, MapLegend } from "../components/map";
import { OnboardingOverlay } from "../components/onboarding";
import { HeaderBlock, EditorialBlock, TemporalBlock, UserControls } from "../components/shell";
import { Spinner, ErrorState } from "../components/common";
import { AboutModal } from "../components/about";
import styles from "./MainView.module.css";

export function MainView() {
  const [lang] = useLang();
  const { seen, dismiss } = useOnboardingSeen();
  const { filters, setFilters, toggleInList } = useFilterState();
  const [searchParams] = useSearchParams();

  const [searchQuery, setSearchQuery] = useState("");
  const [aboutOpen, setAboutOpen] = useState(false);

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

  // Reported by MapLegend so the map's fullscreen/zoom/attribution controls (vertically
  // centred on the right edge) stay clear of it on short viewports — see MapView's
  // legendHeight prop, used as a safe-zone bound rather than a stacking anchor.
  const [legendHeight, setLegendHeight] = useState(0);

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
  });
  const geojsonQuery = useEventsGeoJSON({ channel: filters.channel ?? undefined });
  const ongoingQuery = useOngoingEvents();
  const upcomingQuery = useUpcomingEvents();

  const events = eventsQuery.data ?? [];
  const q = searchQuery.trim().toLowerCase();
  const filteredEvents = q
    ? events.filter((e) => (lang === "el" ? e.summary_el : e.summary_en)?.toLowerCase().includes(q))
    : events;

  const geoFeatures = applyClientFilters(
    (geojsonQuery.data?.features ?? []).map((f) => ({ ...f.properties, feature: f })),
    filters,
  ).map((p) => p.feature);

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
            onReadMorePopup={mode === "list" ? handleReadMore : undefined}
            onClosePopup={handleClosePopup}
            obstructedLeft={sidebarWidth}
            legendHeight={legendHeight}
          />
        )}
        <MapLegend onHeightChange={setLegendHeight} />
      </div>

      <div className={styles.blocks} ref={sidebarRef}>
        <div className={styles.headerBlock}>
          <HeaderBlock
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
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

          <div className={styles.editorialBlock}>
            <EditorialBlock
              mode={mode}
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
        <Footer onAbout={() => setAboutOpen(true)} />
      </div>

      <div className={styles.topRightControls}>
        <UserControls />
      </div>

      {!seen && (
        <OnboardingOverlay
          onDismiss={dismiss}
          onMethodology={() => {
            dismiss();
            setAboutOpen(true);
          }}
        />
      )}

      <AboutModal open={aboutOpen} onClose={() => setAboutOpen(false)} />
    </div>
  );
}

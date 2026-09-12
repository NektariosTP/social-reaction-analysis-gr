import { useEffect, useRef, useState } from "react";
import { useParams, useNavigate, useSearchParams } from "react-router-dom";
import { useEvents, useEventsGeoJSON, useOngoingEvents, useUpcomingEvents, applyClientFilters } from "../api/queries";
import { useFilterState, timeRangeToDateFrom } from "../hooks/useFilterState";
import { useLang } from "../hooks/useLang";
import { useOnboardingSeen } from "../hooks/useOnboardingSeen";
import { Footer } from "../components/layout";
import { MapView, MapLegend } from "../components/map";
import { OnboardingOverlay } from "../components/onboarding";
import {
  HeaderBlock,
  EditorialBlock,
  TemporalBlock,
  UserControls,
  BottomSheet,
  BottomNav,
  LegendPanel,
  type SheetTab,
} from "../components/shell";
import { Spinner, ErrorState } from "../components/common";
import { AboutModal, AboutContent } from "../components/about";
import { useIsMobile } from "../hooks/useIsMobile";
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

  // Reported by MapLegend (desktop only) so the map's fullscreen/zoom/attribution
  // controls stay clear of it on short viewports.
  const [legendHeight, setLegendHeight] = useState(0);

  const isMobile = useIsMobile();
  const [activeTab, setActiveTab] = useState<SheetTab>("temporal");
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // Measured so MapView can keep the initial view (and the mobile attribution
  // control) clear of the pinned header — same ResizeObserver idiom as sidebarWidth.
  const mobileHeaderRef = useRef<HTMLDivElement>(null);
  const [mobileHeaderHeight, setMobileHeaderHeight] = useState(0);
  useEffect(() => {
    const el = mobileHeaderRef.current;
    if (!el || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(([entry]) => setMobileHeaderHeight(entry.contentRect.height));
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const [bottomNavHeight, setBottomNavHeight] = useState(0);

  // BottomSheet's peek height is 36vh (see BottomSheet.module.css .sheet) —
  // kept in sync here so the map's mobile padding doesn't clip the country
  // behind the sheet+nav on initial load.
  const [viewportHeight, setViewportHeight] = useState(() =>
    typeof window === "undefined" ? 0 : window.innerHeight,
  );
  useEffect(() => {
    function onResize() {
      setViewportHeight(window.innerHeight);
    }
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);
  const bottomInset = bottomNavHeight + Math.round(viewportHeight * 0.36);

  // Mobile selection is inline (no /cluster/:id route): toggle the open event.
  function handleMobileSelect(id: string) {
    setExpandedId((cur) => (cur === id ? null : id));
  }
  // Map tap on mobile: open in the Feed tab and expand it.
  function handleMobileSelectFromMap(id: string) {
    setExpandedId(id);
    setActiveTab("feed");
  }
  // Switching tabs collapses any open event.
  function handleTabChange(tab: SheetTab) {
    setActiveTab(tab);
    setExpandedId(null);
  }
  function handleMethodology() {
    dismiss();
    if (isMobile) setActiveTab("about");
    else setAboutOpen(true);
  }

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
            onSelectEvent={isMobile ? handleMobileSelectFromMap : handleSelectEventFromMap}
            selectedId={isMobile ? expandedId : mapSelectedId}
            onReadMorePopup={mode === "list" ? handleReadMore : undefined}
            onClosePopup={handleClosePopup}
            obstructedLeft={isMobile ? 0 : sidebarWidth}
            legendHeight={legendHeight}
            showPopup={!isMobile}
            headerHeight={isMobile ? mobileHeaderHeight : 0}
            bottomInset={isMobile ? bottomInset : 0}
          />
        )}
        {!isMobile && <MapLegend onHeightChange={setLegendHeight} />}
      </div>

      {isMobile ? (
        <>
          <div className={styles.mobileHeader} ref={mobileHeaderRef}>
            <HeaderBlock
              searchQuery={searchQuery}
              onSearchChange={setSearchQuery}
              filters={filters}
              onToggleFilterValue={toggleInList}
              onSetFilters={setFilters}
              trailing={<UserControls />}
            />
          </div>

          <BottomSheet bottomOffset={bottomNavHeight}>
            {activeTab === "temporal" && (
              <TemporalBlock
                ongoing={ongoingQuery.data ?? []}
                upcoming={upcomingQuery.data ?? []}
                loading={ongoingQuery.isLoading || upcomingQuery.isLoading}
                error={ongoingQuery.isError || upcomingQuery.isError}
                expandedId={expandedId}
                onSelectEvent={handleMobileSelect}
              />
            )}
            {activeTab === "feed" && (
              <EditorialBlock
                mode="list"
                events={filteredEvents}
                eventsLoading={eventsQuery.isLoading}
                eventsError={eventsQuery.isError}
                highlightedEventId={expandedId}
                expandedId={expandedId}
                onSelectEvent={handleMobileSelect}
              />
            )}
            {activeTab === "legend" && <LegendPanel />}
            {activeTab === "about" && <AboutContent />}
          </BottomSheet>

          <BottomNav active={activeTab} onChange={handleTabChange} onHeightChange={setBottomNavHeight} />
        </>
      ) : (
        <>
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

          <AboutModal open={aboutOpen} onClose={() => setAboutOpen(false)} />
        </>
      )}

      {!seen && <OnboardingOverlay onDismiss={dismiss} onMethodology={handleMethodology} />}
    </div>
  );
}

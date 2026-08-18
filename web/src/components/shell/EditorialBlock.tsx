import { useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import type { EventSummary } from "../../client/types.gen";
import { StoryCard } from "../cards";
import { ClusterDetailContent } from "../cluster";
import { Spinner, ErrorState, EmptyState } from "../common";
import styles from "./EditorialBlock.module.css";

interface KpiValues {
  active: number | string;
  locations: number;
  newLastHour: number | string;
}

export interface EditorialBlockListProps {
  mode: "list";
  kpi: KpiValues;
  events: EventSummary[];
  eventsLoading: boolean;
  eventsError: boolean;
  highlightedEventId: string | null;
  onSelectEvent: (id: string) => void;
}

interface EditorialBlockDetailProps {
  mode: "detail";
  detailEventId: string;
  onBack: () => void;
}

type EditorialBlockProps = (EditorialBlockListProps | EditorialBlockDetailProps) & {
  onBack?: () => void;
};

export function EditorialBlock(props: EditorialBlockProps) {
  const { t } = useTranslation();
  const listRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (props.mode !== "list" || !props.highlightedEventId || !listRef.current) return;
    const el = listRef.current.querySelector<HTMLElement>(
      `[data-event-id="${props.highlightedEventId}"]`,
    );
    el?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [props.mode, props.mode === "list" ? props.highlightedEventId : null]);

  if (props.mode === "detail") {
    return (
      <div className={styles.block}>
        <button className={styles.backBtn} onClick={props.onBack}>
          {t("editorial.back")}
        </button>
        <ClusterDetailContent eventId={props.detailEventId} />
      </div>
    );
  }

  const { kpi, events, eventsLoading, eventsError, highlightedEventId, onSelectEvent } = props;

  return (
    <div className={styles.block}>
      <div className={styles.kpiStrip}>
        <div className={styles.kpiCell}>
          <div className={styles.kpiValue}>{kpi.active}</div>
          <div className={styles.kpiLabel}>{t("kpi.active")}</div>
        </div>
        <div className={styles.kpiCell}>
          <div className={styles.kpiValue}>{kpi.locations}</div>
          <div className={styles.kpiLabel}>{t("kpi.locations")}</div>
        </div>
        <div className={styles.kpiCell}>
          <div className={styles.kpiValue}>+{kpi.newLastHour}</div>
          <div className={styles.kpiLabel}>{t("kpi.newLastHour")}</div>
        </div>
      </div>
      <div className={styles.feedHeader}>
        <span>{t("feed.title")}</span>
        <span>
          {t("feed.nlpClustered")} · {events.length}
        </span>
      </div>
      <div className={styles.feedList} ref={listRef}>
        {eventsLoading && <Spinner />}
        {eventsError && <ErrorState />}
        {!eventsLoading && !eventsError && events.length === 0 && <EmptyState />}
        {events.map((e, i) => (
          <div
            key={e.id}
            data-event-id={e.id}
            data-highlighted={e.id === highlightedEventId ? "true" : undefined}
            className={e.id === highlightedEventId ? styles.highlighted : undefined}
          >
            <StoryCard
              event={e}
              variant={i === 0 ? "featured" : "compact"}
              onOpen={onSelectEvent}
            />
          </div>
        ))}
      </div>
    </div>
  );
}

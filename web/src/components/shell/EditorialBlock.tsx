import { useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import type { EventSummary } from "../../client/types.gen";
import { StoryCard } from "../cards";
import { ClusterDetailContent } from "../cluster";
import { Spinner, ErrorState, EmptyState } from "../common";
import styles from "./EditorialBlock.module.css";

export interface EditorialBlockListProps {
  mode: "list";
  events: EventSummary[];
  eventsLoading: boolean;
  eventsError: boolean;
  highlightedEventId: string | null;
  onSelectEvent: (id: string) => void;
  expandedId?: string | null;
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

  const { events, eventsLoading, eventsError, highlightedEventId, onSelectEvent, expandedId } = props;
  const articles = events.reduce((sum, e) => sum + (e.article_count ?? 0), 0);

  return (
    <div className={styles.block}>
      <div className={styles.kpiStrip}>
        <div className={styles.kpiCell}>
          <div className={styles.kpiValue}>{events.length}</div>
          <div className={styles.kpiLabel}>{t("kpi.events")}</div>
        </div>
        <div className={styles.kpiCell}>
          <div className={styles.kpiValue}>{articles}</div>
          <div className={styles.kpiLabel}>{t("kpi.articles")}</div>
        </div>
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
            {expandedId === e.id && (
              <div className={styles.inlineDetail} data-inline-detail={e.id}>
                <ClusterDetailContent eventId={e.id} />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

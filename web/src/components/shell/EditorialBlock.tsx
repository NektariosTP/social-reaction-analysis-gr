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

  const { events, eventsLoading, eventsError, highlightedEventId, onSelectEvent } = props;
  const articles = events.reduce((sum, e) => sum + (e.article_count ?? 0), 0);
  const sources = events.reduce((sum, e) => sum + (e.source_count ?? 0), 0);

  return (
    <div className={styles.block}>
      <div className={styles.feedHeader}>
        <span>{t("feed.title")}</span>
        <span className={styles.feedCount}>{events.length}</span>
      </div>
      <div className={styles.feedSummary}>{t("feed.summary", { articles, sources })}</div>
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

import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { EventSummary } from "../../client/types.gen";
import { partitionByNational } from "../../api/queries";
import { useLang } from "../../hooks/useLang";
import { formatRelativeTime } from "../../utils/time";
import { Spinner, ErrorState, EmptyState } from "../common";
import styles from "./TemporalBlock.module.css";

type Tab = "ongoing" | "upcoming";

interface TemporalBlockProps {
  ongoing: EventSummary[];
  upcoming: EventSummary[];
  loading: boolean;
  error: boolean;
  onSelectEvent: (id: string) => void;
}

function TemporalEventRow({
  event,
  kind,
  onSelect,
}: {
  event: EventSummary;
  kind: Tab;
  onSelect: (id: string) => void;
}) {
  const { t } = useTranslation();
  const [lang] = useLang();
  const summary = lang === "el" ? event.summary_el : event.summary_en;
  const chip = kind === "ongoing" ? t("temporal.today") : formatRelativeTime(event.event_time, lang);
  return (
    <button
      type="button"
      className={styles.row}
      data-event-id={event.id}
      onClick={() => onSelect(event.id)}
    >
      <span className={styles.rowChip}>{chip}</span>
      {event.announced_by && (
        <span className={styles.rowChip} data-announced>
          📣 {event.announced_by}
          {event.participating_unions && event.participating_unions.length > 1 && (
            <> · joined by {event.participating_unions.slice(1, 3).join(", ")}
              {event.participating_unions.length > 3
                ? ` +${event.participating_unions.length - 3}` : ""}</>
          )}
        </span>
      )}
      <span className={styles.rowSummary}>{summary}</span>
    </button>
  );
}

export function TemporalBlock({ ongoing, upcoming, loading, error, onSelectEvent }: TemporalBlockProps) {
  const { t } = useTranslation();
  const [manualTab, setManualTab] = useState<Tab | null>(null);
  const activeTab: Tab = manualTab ?? (ongoing.length > 0 ? "ongoing" : "upcoming");
  const { panhellenic, other } = partitionByNational(ongoing);

  return (
    <div className={styles.block}>
      <div className={styles.tabs}>
        <button
          type="button"
          className={`${styles.tab} ${activeTab === "ongoing" ? styles.tabActive : ""}`}
          onClick={() => setManualTab("ongoing")}
        >
          {t("temporal.ongoing")} ({ongoing.length})
        </button>
        <button
          type="button"
          className={`${styles.tab} ${activeTab === "upcoming" ? styles.tabActive : ""}`}
          onClick={() => setManualTab("upcoming")}
        >
          {t("temporal.upcoming")} ({upcoming.length})
        </button>
      </div>

      <div className={styles.body}>
        {loading && <Spinner />}
        {error && <ErrorState />}

        {!loading && !error && activeTab === "ongoing" && (
          ongoing.length === 0 ? (
            <EmptyState message={t("temporal.emptyOngoing")} />
          ) : (
            <>
              {panhellenic.length > 0 && (
                <section>
                  <h3 className={styles.subhead}>{t("temporal.panhellenic")}</h3>
                  {panhellenic.map((e) => (
                    <TemporalEventRow key={e.id} event={e} kind="ongoing" onSelect={onSelectEvent} />
                  ))}
                </section>
              )}
              {other.length > 0 && (
                <section>
                  <h3 className={styles.subhead}>{t("temporal.other")}</h3>
                  {other.map((e) => (
                    <TemporalEventRow key={e.id} event={e} kind="ongoing" onSelect={onSelectEvent} />
                  ))}
                </section>
              )}
            </>
          )
        )}

        {!loading && !error && activeTab === "upcoming" && (
          upcoming.length === 0 ? (
            <EmptyState message={t("temporal.emptyUpcoming")} />
          ) : (
            upcoming.map((e) => (
              <TemporalEventRow key={e.id} event={e} kind="upcoming" onSelect={onSelectEvent} />
            ))
          )
        )}
      </div>
    </div>
  );
}

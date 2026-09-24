import { useTranslation } from "react-i18next";
import type { EventSummary } from "../../client/types.gen";
import { useLang } from "../../hooks/useLang";
import { daysUntil, formatAbsoluteDate } from "../../utils/time";
import styles from "./TemporalBanner.module.css";

interface TemporalBannerProps {
  event: EventSummary;
}

/**
 * Highlighted strip carrying an event's scheduled-time and calling-unions
 * info, pinned atop its story card and shown on the analysis page. Upcoming,
 * today, and past each get a distinct, unambiguous full-sentence message
 * (anchored on event_time, else first_seen for past events). Renders nothing
 * when the event has neither a temporal line nor unions.
 */
export function TemporalBanner({ event }: TemporalBannerProps) {
  const { t } = useTranslation();
  const [lang] = useLang();

  const unions = event.participating_unions ?? [];
  const hasUnions = Boolean(event.announced_by) || unions.length > 0;
  const pastDate = event.event_time ?? event.first_seen ?? null;

  let timeChip: string | null = null;
  if (event.temporal_status === "today") {
    timeChip = `🔴 ${t("banner.happeningToday")}`;
  } else if (event.temporal_status === "upcoming" && event.event_time) {
    const days = daysUntil(event.event_time);
    timeChip = `📅 ${days === 1 ? t("banner.scheduledInOne") : t("banner.scheduledIn", { days })}`;
  } else if (pastDate) {
    timeChip = `📅 ${t("banner.tookPlaceOn", { date: formatAbsoluteDate(pastDate, lang) })}`;
  }

  if (!timeChip && !hasUnions) return null;

  const joinedBy = unions.slice(1, 3);
  const extra = unions.length > 3 ? ` +${unions.length - 3}` : "";

  return (
    <div className={styles.banner}>
      {timeChip && <span className={styles.timeChip}>{timeChip}</span>}
      {event.announced_by && (
        <span className={styles.unions}>
          📣 {event.announced_by}
          {joinedBy.length > 0 && (
            <> · {t("banner.joinedBy", { names: joinedBy.join(", ") })}{extra}</>
          )}
        </span>
      )}
    </div>
  );
}

import { useTranslation } from "react-i18next";
import type { EventSummary } from "../../client/types.gen";
import { useLang } from "../../hooks/useLang";
import { formatRelativeTime } from "../../utils/time";
import styles from "./TemporalBanner.module.css";

interface TemporalBannerProps {
  event: EventSummary;
}

/**
 * Highlighted strip carrying an event's scheduled-time and calling-unions info,
 * pinned atop its story card and shown on the analysis page. Renders nothing
 * when the event has neither a scheduled time nor participating unions.
 */
export function TemporalBanner({ event }: TemporalBannerProps) {
  const { t } = useTranslation();
  const [lang] = useLang();

  const hasTime = Boolean(event.event_time);
  const unions = event.participating_unions ?? [];
  const hasUnions = Boolean(event.announced_by) || unions.length > 0;
  if (!hasTime && !hasUnions) return null;

  const timeChip =
    event.temporal_status === "today"
      ? `🔴 ${t("banner.today")}`
      : hasTime
        ? `📅 ${formatRelativeTime(event.event_time, lang)}`
        : null;

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

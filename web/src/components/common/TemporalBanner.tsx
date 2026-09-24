import { useTranslation } from "react-i18next";
import type { EventSummary } from "../../client/types.gen";
import { useLang } from "../../hooks/useLang";
import { daysUntil, formatAbsoluteDate } from "../../utils/time";
import styles from "./TemporalBanner.module.css";

interface TemporalBannerProps {
  event: EventSummary;
}

type Tone = "upcoming" | "today" | "past";

/**
 * Temporal strip atop a story card / on the analysis page. Upcoming and today
 * events get an emphasized announcement; past events get a quiet "took place on"
 * line (anchored on event_time, else first_seen). Also carries calling-union
 * info. Renders nothing when there is no temporal line and no unions.
 */
export function TemporalBanner({ event }: TemporalBannerProps) {
  const { t } = useTranslation();
  const [lang] = useLang();

  const unions = event.participating_unions ?? [];
  const hasUnions = Boolean(event.announced_by) || unions.length > 0;
  const pastDate = event.event_time ?? event.first_seen ?? null;

  let tone: Tone | null = null;
  let text: string | null = null;
  if (event.temporal_status === "today") {
    tone = "today";
    text = t("banner.happeningToday");
  } else if (event.temporal_status === "upcoming" && event.event_time) {
    tone = "upcoming";
    text = t("banner.scheduledIn", { days: daysUntil(event.event_time) });
  } else if (pastDate) {
    tone = "past";
    text = t("banner.tookPlaceOn", { date: formatAbsoluteDate(pastDate, lang) });
  }

  if (!text && !hasUnions) return null;

  const joinedBy = unions.slice(1, 3);
  const extra = unions.length > 3 ? ` +${unions.length - 3}` : "";

  return (
    <div className={styles.banner} data-tone={tone ?? undefined}>
      {text && <span className={styles.timeLine}>{text}</span>}
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

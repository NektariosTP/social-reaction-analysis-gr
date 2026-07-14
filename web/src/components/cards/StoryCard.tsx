import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import type { EventSummary } from "../../client/types.gen";
import { useLang } from "../../hooks/useLang";
import { formatRelativeTime } from "../../utils/time";
import { AxisTag, IntensityDots } from "../common";
import { PoliticianQuote } from "./PoliticianQuote";
import { TrendingHashtags } from "./TrendingHashtags";
import styles from "./StoryCard.module.css";

interface StoryCardProps {
  event: EventSummary;
  variant?: "featured" | "compact";
}

export function StoryCard({ event, variant = "compact" }: StoryCardProps) {
  const { t } = useTranslation();
  const [lang] = useLang();
  const summary = lang === "el" ? event.summary_el : event.summary_en;
  const isFeatured = variant === "featured";

  return (
    <Link to={`/cluster/${event.id}`} className={styles.card}>
      <div className={styles.tags}>
        {event.action_forms.map((v) => (
          <AxisTag key={v} value={v} variant="action" />
        ))}
        {event.thematic_fields.map((v) => (
          <AxisTag key={v} value={v} variant="theme" />
        ))}
        {event.channel && <AxisTag value={event.channel} variant="channel" />}
        <IntensityDots value={event.intensity} />
      </div>

      <div className={`${styles.headline} ${isFeatured ? "" : styles.headlineCompact}`}>
        {summary ?? "…"}
      </div>

      {isFeatured && (
        <div className={styles.stack}>
          <PoliticianQuote />
          <TrendingHashtags />
        </div>
      )}

      <div className={styles.meta}>
        {event.source_count} {t("card.sources")} · {formatRelativeTime(event.last_seen, lang)}
        {event.region_code ? ` · ${event.region_code}` : ""}
      </div>

      {isFeatured && <div className={styles.cta}>{t("card.viewFullAnalysis")}</div>}
    </Link>
  );
}

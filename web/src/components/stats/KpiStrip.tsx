import { useTranslation } from "react-i18next";
import styles from "./KpiStrip.module.css";

interface KpiStripProps {
  totalEvents: number;
  totalArticles: number;
  locationsCovered: number;
  avgNewPerDay: number;
}

export function KpiStrip({ totalEvents, totalArticles, locationsCovered, avgNewPerDay }: KpiStripProps) {
  const { t } = useTranslation();
  const cells: [string, string][] = [
    [totalEvents.toLocaleString(), t("stats.totalReactions")],
    [totalArticles.toLocaleString(), t("stats.totalArticles")],
    [locationsCovered.toLocaleString(), t("stats.locationsCovered")],
    [`+${avgNewPerDay.toFixed(1)}`, "avg. new events / day"],
  ];

  return (
    <div className={styles.strip}>
      {cells.map(([value, label]) => (
        <div className={styles.cell} key={label}>
          <div className={styles.value}>{value}</div>
          <div className={styles.label}>{label}</div>
        </div>
      ))}
    </div>
  );
}

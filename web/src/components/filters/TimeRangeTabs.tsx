import { useTranslation } from "react-i18next";
import type { TimeRange } from "../../hooks/useFilterState";
import styles from "./TimeRangeTabs.module.css";

const LABEL_KEY: Record<TimeRange, string> = {
  "24h": "time.24h",
  "7d": "time.7d",
  "30d": "time.30d",
  all: "time.all",
};

interface TimeRangeTabsProps {
  value: TimeRange;
  onChange: (value: TimeRange) => void;
  ranges?: TimeRange[];
}

export function TimeRangeTabs({ value, onChange, ranges = ["24h", "7d", "30d", "all"] }: TimeRangeTabsProps) {
  const { t } = useTranslation();
  return (
    <div className={styles.tabs}>
      {ranges.map((range) => (
        <button
          key={range}
          type="button"
          className={`${styles.tab} ${value === range ? styles.tabActive : ""}`}
          onClick={() => onChange(range)}
        >
          {t(LABEL_KEY[range])}
        </button>
      ))}
    </div>
  );
}

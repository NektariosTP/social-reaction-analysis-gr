import { useTranslation } from "react-i18next";
import styles from "./RangePanel.module.css";

interface RangePanelProps {
  windowDays: number | null;
  day: string | null;
  onChange: (next: { windowDays: number | null; day: string | null }) => void;
}

const PRESETS = [7, 15, 30] as const;

/** The time-range control's content — rendered inline by HeaderBlock inside
 * its shared expansion slot, the same way FilterPanel is. */
export function RangePanel({ windowDays, day, onChange }: RangePanelProps) {
  const { t } = useTranslation();

  const presetLabel = (n: number) =>
    n === 7 ? t("range.last7") : n === 15 ? t("range.last15") : t("range.last30");

  return (
    <div className={styles.panel}>
      <button
        type="button"
        className={styles.option}
        data-active={(windowDays === null && !day) || undefined}
        onClick={() => onChange({ windowDays: null, day: null })}
      >
        {t("range.live")}
        <span className={styles.sub}>{t("range.liveSubtitle")}</span>
      </button>
      {PRESETS.map((n) => (
        <button
          key={n}
          type="button"
          className={styles.option}
          data-active={windowDays === n || undefined}
          onClick={() => onChange({ windowDays: n, day: null })}
        >
          {presetLabel(n)}
        </button>
      ))}
      <label className={styles.dateRow}>
        <span>{t("range.exactDate")}</span>
        <input
          type="date"
          value={day ?? ""}
          onChange={(e) => onChange({ windowDays: null, day: e.target.value || null })}
        />
      </label>
    </div>
  );
}

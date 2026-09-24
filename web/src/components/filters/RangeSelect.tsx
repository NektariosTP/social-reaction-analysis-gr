import { useTranslation } from "react-i18next";
import { formatAbsoluteDate } from "../../utils/time";
import { useLang } from "../../hooks/useLang";
import styles from "./RangeSelect.module.css";

interface RangeSelectProps {
  windowDays: number | null;
  day: string | null;
  /** Whether the RangePanel is currently expanded (parent-controlled, mutually
   * exclusive with the Filters panel — both share HeaderBlock's expansion slot). */
  open: boolean;
  onClick: () => void;
}

/** The time-range trigger button. Its content panel (RangePanel) is rendered
 * separately by HeaderBlock, inline in the shared expansion area — matching
 * the Filters trigger/panel split so both controls look and behave alike. */
export function RangeSelect({ windowDays, day, open, onClick }: RangeSelectProps) {
  const { t } = useTranslation();
  const [lang] = useLang();

  const presetLabel = (n: number) =>
    n === 7 ? t("range.last7") : n === 15 ? t("range.last15") : t("range.last30");

  const triggerLabel = day
    ? formatAbsoluteDate(day, lang)
    : windowDays
      ? presetLabel(windowDays)
      : t("range.live");

  return (
    <button type="button" className={styles.trigger} onClick={onClick} aria-expanded={open}>
      <span className={styles.icon}>📅</span>
      <span className={styles.label}>{triggerLabel}</span>
      <span className={styles.arrow}>{open ? "▴" : "▾"}</span>
    </button>
  );
}

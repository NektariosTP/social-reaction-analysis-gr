import { useTranslation } from "react-i18next";
import { useLang } from "../../hooks/useLang";
import { axisLabel } from "../../i18n";
import { ACTION_FORM_ICONS } from "../../i18n/actionFormIcons";
import type { ChipAxis } from "../common/AxisValueChip";
import type { FilterState } from "../../hooks/useFilterState";
import { formatAbsoluteDate } from "../../utils/time";
import styles from "./ActiveFilterPills.module.css";

interface ActiveFilterPillsProps {
  filters: FilterState;
  onToggleFilterValue: (key: "actionForms" | "thematicFields", value: string) => void;
  onSetFilters: (next: Partial<FilterState>) => void;
}

interface Pill {
  key: string;
  value: string;
  label: string;
  /** Colors the pill like its legend chip. null for the range pill, which has
   * no legend equivalent. */
  axis: ChipAxis | null;
  onRemove: () => void;
}

export function ActiveFilterPills({ filters, onToggleFilterValue, onSetFilters }: ActiveFilterPillsProps) {
  const { t } = useTranslation();
  const [lang] = useLang();
  const pills: Pill[] = [];

  for (const v of filters.actionForms) {
    pills.push({
      key: `a1:${v}`,
      value: v,
      label: axisLabel(v, lang),
      axis: "action",
      onRemove: () => onToggleFilterValue("actionForms", v),
    });
  }
  for (const v of filters.thematicFields) {
    pills.push({
      key: `a2:${v}`,
      value: v,
      label: axisLabel(v, lang),
      axis: "theme",
      onRemove: () => onToggleFilterValue("thematicFields", v),
    });
  }
  if (filters.channel) {
    pills.push({
      key: `a3:${filters.channel}`,
      value: filters.channel,
      label: axisLabel(filters.channel, lang),
      axis: "channel",
      onRemove: () => onSetFilters({ channel: null }),
    });
  }
  if (filters.intensity) {
    pills.push({
      key: `a4:${filters.intensity}`,
      value: filters.intensity,
      label: axisLabel(filters.intensity, lang),
      axis: "intensity",
      onRemove: () => onSetFilters({ intensity: null }),
    });
  }
  if (filters.day) {
    pills.push({
      key: "d",
      value: filters.day,
      label: formatAbsoluteDate(filters.day, lang),
      axis: null,
      onRemove: () => onSetFilters({ day: null, windowDays: null }),
    });
  } else if (filters.windowDays) {
    const label =
      filters.windowDays === 7 ? t("range.last7") : filters.windowDays === 15 ? t("range.last15") : t("range.last30");
    pills.push({
      key: "w",
      value: String(filters.windowDays),
      label,
      axis: null,
      onRemove: () => onSetFilters({ windowDays: null, day: null }),
    });
  }

  if (pills.length === 0) return null;

  return (
    <div className={styles.row}>
      {pills.map((p) => (
        <button
          key={p.key}
          type="button"
          className={`${styles.pill} ${p.axis ? styles[p.axis] : ""}`}
          onClick={p.onRemove}
        >
          {p.axis === "action" && <span className={styles.icon}>{ACTION_FORM_ICONS[p.value] ?? ""}</span>}
          {p.label} <span aria-hidden className={styles.x}>✕</span>
        </button>
      ))}
    </div>
  );
}

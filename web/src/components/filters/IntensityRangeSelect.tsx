import { useTranslation } from "react-i18next";
import { INTENSITY } from "../../i18n/taxonomy";
import { IntensityDots } from "../common";
import type { FilterState } from "../../hooks/useFilterState";
import { toggleWithAllSentinel } from "../../hooks/useFilterState";
import styles from "./AxisMultiSelect.module.css";

interface IntensityRangeSelectProps {
  selected: string[];
  onSetFilters: (next: Partial<FilterState>) => void;
}

const LEVELS = Object.entries(INTENSITY).sort((a, b) => a[1].level - b[1].level);
const ALL_INTENSITY_VALUES = LEVELS.map(([value]) => value);

/** Intensity is ordinal with only 3 discrete values — implemented as a
 * checklist rather than a continuous slider. */
export function IntensityRangeSelect({ selected, onSetFilters }: IntensityRangeSelectProps) {
  const { t } = useTranslation();

  function handleToggle(value: string) {
    onSetFilters({ intensities: toggleWithAllSentinel(ALL_INTENSITY_VALUES, selected, value) });
  }

  return (
    <div className={styles.group}>
      <div className={styles.label}>{t("filters.axis4")}</div>
      <div className={styles.chips} style={{ flexDirection: "column", alignItems: "flex-start" }}>
        {LEVELS.map(([value]) => (
          <label key={value} style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={selected.length === 0 || selected.includes(value)}
              onChange={() => handleToggle(value)}
            />
            <IntensityDots value={value} showLabel />
          </label>
        ))}
      </div>
    </div>
  );
}

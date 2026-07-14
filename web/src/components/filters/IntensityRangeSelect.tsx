import { useTranslation } from "react-i18next";
import { INTENSITY } from "../../i18n/taxonomy";
import { IntensityDots } from "../common";
import styles from "./AxisMultiSelect.module.css";

interface IntensityRangeSelectProps {
  selected: string[];
  onToggle: (value: string) => void;
}

const LEVELS = Object.entries(INTENSITY).sort((a, b) => a[1].level - b[1].level);

/** Intensity is ordinal with only 3 discrete values — implemented as a
 * checklist rather than a continuous slider. */
export function IntensityRangeSelect({ selected, onToggle }: IntensityRangeSelectProps) {
  const { t } = useTranslation();

  return (
    <div className={styles.group}>
      <div className={styles.label}>{t("filters.axis4")}</div>
      <div className={styles.chips} style={{ flexDirection: "column", alignItems: "flex-start" }}>
        {LEVELS.map(([value]) => (
          <label key={value} style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }}>
            <input
              type="checkbox"
              checked={selected.length === 0 || selected.includes(value)}
              onChange={() => onToggle(value)}
            />
            <IntensityDots value={value} showLabel />
          </label>
        ))}
      </div>
    </div>
  );
}

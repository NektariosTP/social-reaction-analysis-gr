import { useTranslation } from "react-i18next";
import { INTENSITY } from "../../i18n/taxonomy";
import { IntensityDots } from "../common";
import styles from "./AxisMultiSelect.module.css";

interface IntensityRangeSelectProps {
  selected: string | null;
  onChange: (value: string | null) => void;
}

const LEVELS = Object.entries(INTENSITY).sort((a, b) => a[1].level - b[1].level);

/** Single-select, mirroring ChannelSelect: intensity is one value per event,
 * so the filter picks at most one too (All / Peaceful / Disruptive / Violent). */
export function IntensityRangeSelect({ selected, onChange }: IntensityRangeSelectProps) {
  const { t } = useTranslation();

  return (
    <div className={styles.group}>
      <div className={styles.label}>{t("filters.axis4")}</div>
      <div className={styles.chips}>
        <button
          type="button"
          className={`${styles.chip} ${!selected ? styles.chipSelected : ""}`}
          onClick={() => onChange(null)}
        >
          {t("filters.all")}
        </button>
        {LEVELS.map(([value]) => (
          <button
            key={value}
            type="button"
            className={`${styles.chip} ${selected === value ? styles.chipSelected : ""}`}
            onClick={() => onChange(value)}
          >
            <IntensityDots value={value} showLabel />
          </button>
        ))}
      </div>
    </div>
  );
}

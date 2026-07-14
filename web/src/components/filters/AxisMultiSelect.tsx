import { useTranslation } from "react-i18next";
import { useLang } from "../../hooks/useLang";
import { axisLabel } from "../../i18n";
import styles from "./AxisMultiSelect.module.css";

interface AxisMultiSelectProps {
  title: string;
  options: string[];
  selected: string[];
  onToggle: (value: string) => void;
  onClear: () => void;
}

export function AxisMultiSelect({ title, options, selected, onToggle, onClear }: AxisMultiSelectProps) {
  const { t } = useTranslation();
  const [lang] = useLang();
  const allSelected = selected.length === 0;

  return (
    <div className={styles.group}>
      <div className={styles.label}>{title}</div>
      <div className={styles.chips}>
        <button
          type="button"
          className={`${styles.chip} ${allSelected ? styles.chipSelected : ""}`}
          onClick={onClear}
        >
          {t("filters.all")}
        </button>
        {options.map((value) => (
          <button
            key={value}
            type="button"
            className={`${styles.chip} ${selected.includes(value) ? styles.chipSelected : ""}`}
            onClick={() => onToggle(value)}
          >
            {axisLabel(value, lang)}
          </button>
        ))}
      </div>
    </div>
  );
}

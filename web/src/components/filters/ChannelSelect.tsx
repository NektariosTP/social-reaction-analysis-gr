import { useTranslation } from "react-i18next";
import { useLang } from "../../hooks/useLang";
import { axisLabel } from "../../i18n";
import { CHANNEL } from "../../i18n/taxonomy";
import styles from "./AxisMultiSelect.module.css";

interface ChannelSelectProps {
  selected: string | null;
  onChange: (value: string | null) => void;
}

export function ChannelSelect({ selected, onChange }: ChannelSelectProps) {
  const { t } = useTranslation();
  const [lang] = useLang();
  const options = Object.keys(CHANNEL);

  return (
    <div className={styles.group}>
      <div className={styles.label}>{t("filters.axis3")}</div>
      <div className={styles.chips}>
        <button
          type="button"
          className={`${styles.chip} ${!selected ? styles.chipSelected : ""}`}
          onClick={() => onChange(null)}
        >
          {t("filters.all")}
        </button>
        {options.map((value) => (
          <button
            key={value}
            type="button"
            className={`${styles.chip} ${selected === value ? styles.chipSelected : ""}`}
            onClick={() => onChange(value)}
          >
            {axisLabel(value, lang)}
          </button>
        ))}
      </div>
    </div>
  );
}

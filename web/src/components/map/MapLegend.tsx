import { useTranslation } from "react-i18next";
import { useLang } from "../../hooks/useLang";
import { axisLabel } from "../../i18n";
import { INTENSITY } from "../../i18n/taxonomy";
import { INTENSITY_COLORS } from "./bubbleColors";
import styles from "./MapLegend.module.css";

const LEVELS = Object.entries(INTENSITY).sort((a, b) => a[1].level - b[1].level);

export function MapLegend() {
  const { t } = useTranslation();
  const [lang] = useLang();
  return (
    <div className={styles.legend}>
      <div className={styles.title}>{t("filters.axis4")}</div>
      {LEVELS.map(([value, entry]) => (
        <div className={styles.row} key={value}>
          <span className={styles.dot} style={{ borderColor: INTENSITY_COLORS[entry.level] }} />
          <span>{axisLabel(value, lang)}</span>
        </div>
      ))}
      <div className={styles.hint}>size = article count</div>
    </div>
  );
}

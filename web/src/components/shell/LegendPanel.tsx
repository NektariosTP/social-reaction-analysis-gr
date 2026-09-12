import { useTranslation } from "react-i18next";
import { LegendContent } from "../map/LegendContent";
import styles from "./LegendPanel.module.css";

/** Mobile "Legend" bottom-nav tab body — the shared axis reference content
 * with no toggle, since tapping the tab already made the choice to view it. */
export function LegendPanel() {
  const { t } = useTranslation();
  return (
    <div className={styles.panel}>
      <div className={styles.heading}>{t("legend.title")}</div>
      <LegendContent />
    </div>
  );
}

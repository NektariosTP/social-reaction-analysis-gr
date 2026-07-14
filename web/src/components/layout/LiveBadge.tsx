import { useTranslation } from "react-i18next";
import styles from "./LiveBadge.module.css";

export function LiveBadge() {
  const { t } = useTranslation();
  return (
    <span className={styles.badge}>
      <span className={styles.dot} />
      {t("live")}
    </span>
  );
}

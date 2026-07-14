import { useTranslation } from "react-i18next";
import styles from "./MobileNotice.module.css";

/** Simple responsive fallback — a persistent banner, not the 3 dedicated
 * mobile layouts from wireframe §05 (deprioritized). */
export function MobileNotice() {
  const { t } = useTranslation();
  return <div className={styles.notice}>{t("mobile.notice")}</div>;
}

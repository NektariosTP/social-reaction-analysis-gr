import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useLang } from "../../hooks/useLang";
import { LiveBadge } from "./LiveBadge";
import styles from "./TopBar.module.css";

export function TopBar() {
  const { t } = useTranslation();
  const [lang, setLang] = useLang();

  return (
    <header className={styles.bar}>
      <Link to="/" className={styles.brand}>
        <span className={styles.mark}>R</span>
        <span className={styles.brandName}>{t("brand")}</span>
      </Link>
      <LiveBadge />
      <nav className={styles.nav}>
        <Link to="/">{t("nav.map")}</Link>
        <Link to="/stats">{t("nav.stats")}</Link>
        <Link to="/about">{t("nav.about")}</Link>
      </nav>
      <span className={styles.spacer} />
      <div className={styles.langToggle}>
        <button
          className={lang === "el" ? styles.langActive : ""}
          onClick={() => setLang("el")}
          aria-pressed={lang === "el"}
        >
          EL
        </button>
        <button
          className={lang === "en" ? styles.langActive : ""}
          onClick={() => setLang("en")}
          aria-pressed={lang === "en"}
        >
          EN
        </button>
      </div>
    </header>
  );
}

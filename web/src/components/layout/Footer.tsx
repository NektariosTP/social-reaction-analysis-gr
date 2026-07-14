import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import styles from "./Footer.module.css";

export function Footer() {
  const { t } = useTranslation();
  return (
    <footer className={styles.footer}>
      <span>{t("brand")} · © 2026</span>
      <nav className={styles.links}>
        <Link to="/about">{t("footer.about")}</Link>
        <Link to="/about">{t("footer.methodology")}</Link>
        <a href="https://github.com/" target="_blank" rel="noreferrer">
          {t("footer.github")}
        </a>
      </nav>
    </footer>
  );
}

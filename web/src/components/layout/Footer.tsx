import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import styles from "./Footer.module.css";

const GITHUB_URL = "https://github.com/NektariosTP/social-reaction-analysis-gr";

export function Footer() {
  const { t } = useTranslation();
  return (
    <footer className={styles.footer}>
      <span>{t("brand")} · © 2026</span>
      <nav className={styles.links}>
        <Link to="/about">{t("footer.about")}</Link>
        <a href="#">{t("footer.docs")}</a>
        <a href={GITHUB_URL} target="_blank" rel="noreferrer">
          {t("footer.github")}
        </a>
        <a href="mailto:nektarios.tp@gmail.com">{t("footer.contact")}</a>
        <a href="#">{t("footer.privacy")}</a>
      </nav>
      <span aria-hidden="true" />
    </footer>
  );
}

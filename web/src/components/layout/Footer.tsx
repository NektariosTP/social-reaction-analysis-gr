import { useTranslation } from "react-i18next";
import styles from "./Footer.module.css";

const GITHUB_URL = "https://github.com/NektariosTP/social-reaction-analysis-gr";

interface FooterProps {
  /** Opens the About modal. When omitted, the About link is not rendered. */
  onAbout?: () => void;
}

export function Footer({ onAbout }: FooterProps) {
  const { t } = useTranslation();
  return (
    <footer className={styles.footer}>
      <span>{t("brand")} · © 2026</span>
      <nav className={styles.links}>
        {onAbout && (
          <button type="button" className={styles.linkButton} onClick={onAbout}>
            {t("footer.about")}
          </button>
        )}
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

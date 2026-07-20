import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useLang } from "../../hooks/useLang";
import styles from "./UserControls.module.css";

type OpenPanel = "none" | "login" | "settings";

export function UserControls() {
  const { t } = useTranslation();
  const [lang, setLang] = useLang();
  const [open, setOpen] = useState<OpenPanel>("none");

  return (
    <div className={styles.wrap}>
      <div className={styles.buttons}>
        <button
          className={styles.circle}
          aria-label={t("login.title")}
          onClick={() => setOpen((o) => (o === "login" ? "none" : "login"))}
        >
          👤
        </button>
        <button
          className={styles.circle}
          aria-label={t("settings.title")}
          onClick={() => setOpen((o) => (o === "settings" ? "none" : "settings"))}
        >
          ⚙
        </button>
      </div>

      {open === "login" && (
        <div className={styles.panel}>
          <div className={styles.panelTitle}>{t("login.title")}</div>
          <p className={styles.comingSoon}>{t("comingSoon")}</p>
        </div>
      )}

      {open === "settings" && (
        <div className={styles.panel}>
          <div className={styles.panelTitle}>{t("settings.title")}</div>
          <div className={styles.settingsRow}>
            <span>{t("settings.language")}</span>
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
          </div>
        </div>
      )}
    </div>
  );
}

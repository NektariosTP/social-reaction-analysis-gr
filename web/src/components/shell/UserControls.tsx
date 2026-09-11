import { useLang } from "../../hooks/useLang";
import styles from "./UserControls.module.css";

/** Floating top-right control — just the EL/EN language switch. */
export function UserControls() {
  const [lang, setLang] = useLang();

  return (
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
  );
}

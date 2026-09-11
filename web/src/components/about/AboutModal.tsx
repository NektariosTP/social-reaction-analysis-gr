import { useEffect } from "react";
import { useTranslation } from "react-i18next";
import { AboutContent } from "./AboutContent";
import styles from "./AboutModal.module.css";

interface AboutModalProps {
  open: boolean;
  onClose: () => void;
}

/** Scrollable About / methodology dialog, opened over the map instead of a
 * separate route. Closes on backdrop click, the ✕ button, or Escape. */
export function AboutModal({ open, onClose }: AboutModalProps) {
  const { t } = useTranslation();

  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div className={styles.scrim} onClick={onClose} role="presentation">
      <div
        className={styles.modal}
        role="dialog"
        aria-modal="true"
        aria-label={t("nav.about")}
        onClick={(e) => e.stopPropagation()}
      >
        <button className={styles.close} onClick={onClose} aria-label={t("filters.done")}>
          ✕
        </button>
        <div className={styles.scroll}>
          <AboutContent />
        </div>
      </div>
    </div>
  );
}

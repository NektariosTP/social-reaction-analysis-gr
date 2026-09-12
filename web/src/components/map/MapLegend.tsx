import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { LegendContent } from "./LegendContent";
import styles from "./MapLegend.module.css";

interface MapLegendProps {
  /** Reports the legend's rendered height (px) on mount and whenever it changes
   * (open/close toggle, content), so callers can keep other UI clear of it without
   * hardcoding its height. */
  onHeightChange?: (height: number) => void;
}

/** Desktop-only floating legend widget (bottom-right of the map). On mobile,
 * the equivalent content renders as its own bottom-nav tab — see LegendPanel. */
export function MapLegend({ onHeightChange }: MapLegendProps = {}) {
  const { t } = useTranslation();
  const [open, setOpen] = useState(true);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = rootRef.current;
    if (!el || !onHeightChange || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(([entry]) => onHeightChange(entry.contentRect.height));
    observer.observe(el);
    return () => observer.disconnect();
  }, [onHeightChange]);

  return (
    <div className={styles.legend} ref={rootRef}>
      <button className={styles.toggle} onClick={() => setOpen((o) => !o)} aria-expanded={open}>
        {t("legend.title")} {open ? "▾" : "▸"}
      </button>
      {open && <LegendContent />}
    </div>
  );
}

import { useEffect, useRef } from "react";
import { useTranslation } from "react-i18next";
import styles from "./BottomNav.module.css";

export type SheetTab = "temporal" | "feed" | "legend" | "about";

interface BottomNavProps {
  active: SheetTab;
  onChange: (tab: SheetTab) => void;
  /** Reports the nav's rendered height (px), same idiom as MapLegend's
   * onHeightChange, so callers can keep the sheet and map padding clear of it. */
  onHeightChange?: (height: number) => void;
}

const TABS: { key: SheetTab; icon: string; labelKey: string }[] = [
  { key: "temporal", icon: "📣", labelKey: "sheet.temporal" },
  { key: "feed", icon: "📰", labelKey: "sheet.feed" },
  { key: "legend", icon: "🗺️", labelKey: "legend.title" },
  { key: "about", icon: "ℹ️", labelKey: "nav.about" },
];

/** Mobile-only, Instagram-style persistent bottom navigation: switches which
 * tab's content BottomSheet shows. Pinned to the true bottom of the screen,
 * below the sheet. */
export function BottomNav({ active, onChange, onHeightChange }: BottomNavProps) {
  const { t } = useTranslation();
  const rootRef = useRef<HTMLElement>(null);

  useEffect(() => {
    const el = rootRef.current;
    if (!el || !onHeightChange || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(([entry]) => onHeightChange(entry.contentRect.height));
    observer.observe(el);
    return () => observer.disconnect();
  }, [onHeightChange]);

  return (
    <nav className={styles.nav} data-testid="bottom-nav" ref={rootRef}>
      {TABS.map((tab) => (
        <button
          key={tab.key}
          type="button"
          className={styles.item}
          data-active={tab.key === active ? "true" : undefined}
          aria-current={tab.key === active ? "page" : undefined}
          onClick={() => onChange(tab.key)}
        >
          <span className={styles.icon} aria-hidden="true">
            {tab.icon}
          </span>
          <span className={styles.label}>{t(tab.labelKey)}</span>
        </button>
      ))}
    </nav>
  );
}

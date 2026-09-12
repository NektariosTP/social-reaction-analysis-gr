import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useLang } from "../../hooks/useLang";
import { axisLabel } from "../../i18n";
import { ACTION_FORM, THEMATIC_FIELD, CHANNEL, INTENSITY, CHANNEL_BORDER_STYLE } from "../../i18n/taxonomy";
import { ACTION_FORM_ICONS } from "../../i18n/actionFormIcons";
import { AxisReferenceBlock } from "../common/AxisReferenceBlock";
import { INTENSITY_COLORS } from "./bubbleColors";
import styles from "./MapLegend.module.css";

const LEVELS = Object.entries(INTENSITY).sort((a, b) => a[1].level - b[1].level);
const CHANNEL_VALUES = Object.keys(CHANNEL);
const ACTION_FORM_VALUES = Object.keys(ACTION_FORM);
const THEMATIC_FIELD_VALUES = Object.keys(THEMATIC_FIELD);

interface MapLegendProps {
  /** Reports the legend's rendered height (px) on mount and whenever it changes
   * (open/close toggle, content), so callers can keep other UI clear of it without
   * hardcoding its height. */
  onHeightChange?: (height: number) => void;
}

export function MapLegend({ onHeightChange }: MapLegendProps = {}) {
  const { t } = useTranslation();
  const [lang] = useLang();
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
      {open && (
        <div className={styles.content}>
          <AxisReferenceBlock label={t("filters.axis1")} variant="compact" color="var(--color-axis1)">
            {ACTION_FORM_VALUES.map((value) => (
              <div className={styles.row} key={value}>
                <span className={styles.icon}>{ACTION_FORM_ICONS[value]}</span>
                <span>{axisLabel(value, lang)}</span>
              </div>
            ))}
          </AxisReferenceBlock>
          <AxisReferenceBlock label={t("filters.axis2")} variant="compact" color="var(--color-axis2)">
            {THEMATIC_FIELD_VALUES.map((value) => (
              <div className={styles.row} key={value}>
                <span className={styles.swatch} style={{ background: "var(--color-axis2)" }} />
                <span>{axisLabel(value, lang)}</span>
              </div>
            ))}
          </AxisReferenceBlock>
          <AxisReferenceBlock label={t("filters.axis3")} variant="compact" color="var(--color-axis3)">
            {CHANNEL_VALUES.map((value) => (
              <div className={styles.row} key={value}>
                <span className={styles.borderSample} style={{ borderStyle: CHANNEL_BORDER_STYLE[value] }} />
                <span>{axisLabel(value, lang)}</span>
              </div>
            ))}
          </AxisReferenceBlock>
          <AxisReferenceBlock label={t("filters.axis4")} variant="compact" color="var(--color-axis4-mid)">
            {LEVELS.map(([value, entry]) => (
              <div className={styles.row} key={value}>
                <span className={styles.swatch} style={{ background: INTENSITY_COLORS[entry.level] }} />
                <span>{axisLabel(value, lang)}</span>
              </div>
            ))}
          </AxisReferenceBlock>
          <div className={styles.hint}>{t("legend.countHint")}</div>
        </div>
      )}
    </div>
  );
}

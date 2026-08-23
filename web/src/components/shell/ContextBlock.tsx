import { useTranslation } from "react-i18next";
import { useLang } from "../../hooks/useLang";
import { useRegionIndicators, useIndicatorCatalog } from "../../api/queries";
import type { IndicatorValue } from "../../client/types.gen";
import styles from "./ContextBlock.module.css";

interface ContextBlockProps {
  regionCode: string | null; // null ⇒ national
  title?: string;            // area name when a periphery/municipality is selected
  onClose?: () => void;      // present ⇒ render close button (periphery mode)
  onSelectIndicator?: (key: string | null) => void;
}

function Row({ i, lang }: { i: IndicatorValue; lang: string }) {
  return (
    <li className={styles.row}>
      <span className={styles.label}>{lang === "el" ? i.label_el : i.label_en}</span>
      <span className={styles.value}>
        {i.value == null ? "n/a" : `${i.value}${i.unit && i.unit !== "index" ? ` ${i.unit}` : ""}`}
        {i.period ? <span className={styles.period}> ({i.period})</span> : null}
        {i.source_url ? (
          <a className={styles.src} href={i.source_url} target="_blank" rel="noreferrer">↗</a>
        ) : null}
      </span>
    </li>
  );
}

export function ContextBlock({ regionCode, title, onClose, onSelectIndicator }: ContextBlockProps) {
  const { t } = useTranslation();
  const [lang] = useLang();
  const { data, isLoading, isError } = useRegionIndicators(regionCode ?? "GR");
  const { data: catalog } = useIndicatorCatalog();

  const heading = title ?? t("context.national", "Greece — national context");
  const all = [...(data?.always_on ?? []), ...(data?.thematic ?? [])];
  const periphery = all.filter((i) => i.source === "eurostat");
  const national = all.filter((i) => i.source === "worldbank");
  const catalogItems = catalog?.indicators ?? [];

  const groups: [string, IndicatorValue[]][] = [
    [t("context.peripherySpecific", "Periphery-specific"), periphery],
    [t("context.nationalGreece", "National — Greece"), national],
  ];

  return (
    <div className={styles.block}>
      <div className={styles.header}>
        <span>{heading}</span>
        {onClose && (
          <button type="button" className={styles.close} aria-label="Close area view" onClick={onClose}>×</button>
        )}
      </div>

      {onSelectIndicator && catalogItems.length > 0 && (
        <select
          className={styles.picker}
          aria-label={t("context.mapOverlay", "Show on map")}
          defaultValue=""
          onChange={(e) => onSelectIndicator(e.target.value || null)}
        >
          <option value="">{t("context.mapOverlayNone", "Map overlay: none")}</option>
          {catalogItems.map((i) => (
            <option key={i.key} value={i.key}>{lang === "el" ? i.label_el : i.label_en}</option>
          ))}
        </select>
      )}

      {isLoading ? (
        <p className={styles.empty}>…</p>
      ) : isError || all.length === 0 ? (
        <p className={styles.empty}>{t("context.none", "No context data yet.")}</p>
      ) : (
        groups.map(([label, items]) =>
          items.length === 0 ? null : (
            <div key={label}>
              <div className={styles.groupLabel}>{label}</div>
              <ul className={styles.list}>
                {items.map((i) => <Row key={i.key} i={i} lang={lang} />)}
              </ul>
            </div>
          ),
        )
      )}
      <p className={styles.note}>{t("context.disclaimer", "Descriptive context — correlation, not causation.")}</p>
    </div>
  );
}

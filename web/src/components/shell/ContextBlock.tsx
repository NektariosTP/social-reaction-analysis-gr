import { useTranslation } from "react-i18next";
import { useLang } from "../../hooks/useLang";
import { useRegionIndicators } from "../../api/queries";
import styles from "./ContextBlock.module.css";

interface ContextBlockProps {
  regionCode: string | null;  // null ⇒ national
  onSelectIndicator?: (key: string | null) => void;
}

export function ContextBlock({ regionCode, onSelectIndicator }: ContextBlockProps) {
  const { t } = useTranslation();
  const [lang] = useLang();
  const { data, isLoading, isError } = useRegionIndicators(regionCode ?? "GR");

  const title = regionCode
    ? regionCode
    : t("context.national", "Greece — national context");

  const items = [...(data?.always_on ?? []), ...(data?.thematic ?? [])];

  return (
    <div className={styles.block}>
      <div className={styles.header}>{title}</div>
      {onSelectIndicator && items.length > 0 && (
        <select
          className={styles.picker}
          aria-label={t("context.mapOverlay", "Show on map")}
          defaultValue=""
          onChange={(e) => onSelectIndicator(e.target.value || null)}
        >
          <option value="">{t("context.mapOverlayNone", "Map overlay: none")}</option>
          {items.map((i) => (
            <option key={i.key} value={i.key}>
              {lang === "el" ? i.label_el : i.label_en}
            </option>
          ))}
        </select>
      )}
      {isLoading ? (
        <p className={styles.empty}>…</p>
      ) : isError || items.length === 0 ? (
        <p className={styles.empty}>{t("context.none", "No context data yet.")}</p>
      ) : (
        <ul className={styles.list}>
          {items.map((i) => (
            <li key={i.key} className={styles.row}>
              <span className={styles.label}>{lang === "el" ? i.label_el : i.label_en}</span>
              <span className={styles.value}>
                {i.value == null ? "n/a" : `${i.value}${i.unit && i.unit !== "index" ? ` ${i.unit}` : ""}`}
                {i.period ? <span className={styles.period}> ({i.period})</span> : null}
                {i.source_url ? (
                  <a className={styles.src} href={i.source_url} target="_blank" rel="noreferrer">↗</a>
                ) : null}
              </span>
            </li>
          ))}
        </ul>
      )}
      <p className={styles.note}>{t("context.disclaimer", "Descriptive context — correlation, not causation.")}</p>
    </div>
  );
}

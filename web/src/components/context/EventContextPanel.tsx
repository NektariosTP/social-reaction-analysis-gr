import { useTranslation } from "react-i18next";
import { useLang } from "../../hooks/useLang";
import { useEventContext } from "../../api/queries";
import type { IndicatorValue } from "../../client/types.gen";
import sectionStyles from "../cluster/ClusterDetailContent.module.css";
import styles from "../shell/ContextBlock.module.css";

interface EventContextPanelProps {
  eventId: string;
}

export function EventContextPanel({ eventId }: EventContextPanelProps) {
  const { t } = useTranslation();
  const [lang] = useLang();
  const { data, isLoading } = useEventContext(eventId);
  if (isLoading || !data) return null;

  const all = [...(data.always_on ?? []), ...(data.thematic ?? [])];
  const periphery = all.filter((i) => i.source === "eurostat");
  const national = all.filter((i) => i.source === "worldbank");

  const groups: [string, IndicatorValue[]][] = [
    [`${t("context.peripherySpecific", "Periphery-specific")} — ${data.region_code}`, periphery],
    [t("context.nationalGreece", "National — Greece"), national],
  ];

  return (
    <section aria-label="event-context">
      {groups.map(([heading, items]) =>
        items.length === 0 ? null : (
          <div key={heading} className={sectionStyles.section}>
            <div className={sectionStyles.sectionLabel}>{heading}</div>
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
          </div>
        ),
      )}
      <p className={styles.note}>{t("context.disclaimer", "Descriptive context — correlation, not causation.")}</p>
    </section>
  );
}

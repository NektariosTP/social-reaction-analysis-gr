import { useTranslation } from "react-i18next";
import type { EventDetail } from "../../client/types.gen";
import { AxisTag, IntensityDots } from "../common";
import styles from "./ClassificationTable.module.css";

function fmt(value: unknown): string {
  return typeof value === "number" ? value.toFixed(2) : "—";
}

export function ClassificationTable({ event }: { event: EventDetail }) {
  const { t } = useTranslation();
  const conf = event.classification_confidence ?? {};

  return (
    <div className={styles.table}>
      <div className={styles.headRow}>
        <span>Axis</span>
        <span>Labels</span>
        <span>Conf.</span>
      </div>
      <div className={styles.row}>
        <span className={styles.axisName}>{t("filters.axis1")}</span>
        <span className={styles.tags}>
          {event.action_forms.map((v) => (
            <AxisTag key={v} value={v} variant="action" />
          ))}
        </span>
        <span className={styles.confidence}>{fmt(conf["action_forms"])}</span>
      </div>
      <div className={styles.row}>
        <span className={styles.axisName}>{t("filters.axis2")}</span>
        <span className={styles.tags}>
          {event.thematic_fields.map((v) => (
            <AxisTag key={v} value={v} variant="theme" />
          ))}
        </span>
        <span className={styles.confidence}>{fmt(conf["thematic_fields"])}</span>
      </div>
      <div className={styles.row}>
        <span className={styles.axisName}>{t("filters.axis3")}</span>
        <span className={styles.tags}>
          {event.channel && <AxisTag value={event.channel} variant="channel" />}
        </span>
        <span className={styles.confidence}>{fmt(conf["channel"])}</span>
      </div>
      <div className={styles.row}>
        <span className={styles.axisName}>{t("filters.axis4")}</span>
        <span className={styles.tags}>
          <IntensityDots value={event.intensity} showLabel />
        </span>
        <span className={styles.confidence}>{fmt(conf["intensity"])}</span>
      </div>
    </div>
  );
}

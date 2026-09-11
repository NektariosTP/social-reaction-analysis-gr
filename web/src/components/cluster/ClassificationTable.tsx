import { useTranslation } from "react-i18next";
import type { EventDetail } from "../../client/types.gen";
import { AxisTag } from "../common";
import styles from "./ClassificationTable.module.css";

export function ClassificationTable({ event }: { event: EventDetail }) {
  const { t } = useTranslation();

  return (
    <div className={styles.table}>
      <div className={styles.row}>
        <span className={styles.axisName}>{t("filters.axis1")}</span>
        <span className={styles.tags}>
          {event.action_forms.map((v) => (
            <AxisTag key={v} value={v} variant="action" />
          ))}
        </span>
      </div>
      <div className={styles.row}>
        <span className={styles.axisName}>{t("filters.axis2")}</span>
        <span className={styles.tags}>
          {event.thematic_fields.map((v) => (
            <AxisTag key={v} value={v} variant="theme" />
          ))}
        </span>
      </div>
      <div className={styles.row}>
        <span className={styles.axisName}>{t("filters.axis3")}</span>
        <span className={styles.tags}>
          {event.channel && <AxisTag value={event.channel} variant="channel" />}
        </span>
      </div>
      <div className={styles.row}>
        <span className={styles.axisName}>{t("filters.axis4")}</span>
        <span className={styles.tags}>
          {event.intensity && <AxisTag value={event.intensity} variant="intensity" />}
        </span>
      </div>
    </div>
  );
}

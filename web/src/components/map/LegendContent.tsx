import { useTranslation } from "react-i18next";
import { ACTION_FORM, THEMATIC_FIELD, CHANNEL, INTENSITY } from "../../i18n/taxonomy";
import { AxisReferenceBlock } from "../common/AxisReferenceBlock";
import { AxisValueChip, type ChipAxis } from "../common/AxisValueChip";
import { INTENSITY_COLORS } from "./bubbleColors";
import styles from "./MapLegend.module.css";

const INTENSITY_LEVELS = [1, 2, 3] as const;

const AXES: { titleKey: string; axis: ChipAxis; values: string[]; color: string }[] = [
  { titleKey: "filters.axis1", axis: "action", values: Object.keys(ACTION_FORM), color: "var(--color-axis1)" },
  { titleKey: "filters.axis2", axis: "theme", values: Object.keys(THEMATIC_FIELD), color: "var(--color-axis2)" },
  { titleKey: "filters.axis3", axis: "channel", values: Object.keys(CHANNEL), color: "var(--color-axis3)" },
  { titleKey: "filters.axis4", axis: "intensity", values: Object.keys(INTENSITY), color: "var(--color-axis4-mid)" },
];

/** The legend's axis-reference rows, shared by the desktop floating MapLegend
 * widget and the mobile Legend tab (LegendPanel). Each axis is a colored block
 * of soft-tinted pills — the same pill language used across the app (cards,
 * About, onboarding) so the legend reads as one system. */
export function LegendContent() {
  const { t } = useTranslation();

  return (
    <div className={styles.content}>
      {AXES.map(({ titleKey, axis, values, color }) => (
        <AxisReferenceBlock key={titleKey} label={t(titleKey)} variant="compact" color={color}>
          <div className={styles.chipRow}>
            {values.map((value) => (
              <AxisValueChip key={value} axis={axis} value={value} />
            ))}
          </div>
        </AxisReferenceBlock>
      ))}
      <div className={styles.hint}>{t("legend.countHint")}</div>
      <div className={styles.colorHint}>
        {t("legend.colorHint")}
        <span className={styles.swatchRow}>
          {INTENSITY_LEVELS.map((level) => (
            <span key={level} className={styles.dot} style={{ background: INTENSITY_COLORS[level] }} />
          ))}
        </span>
      </div>
    </div>
  );
}

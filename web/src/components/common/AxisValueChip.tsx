import { useLang } from "../../hooks/useLang";
import { axisLabel, intensityLevel } from "../../i18n";
import { CHANNEL_BORDER_STYLE } from "../../i18n/taxonomy";
import { ACTION_FORM_ICONS } from "../../i18n/actionFormIcons";
import { INTENSITY_COLORS } from "../map/bubbleColors";
import styles from "./AxisValueChip.module.css";

export type ChipAxis = "action" | "theme" | "channel" | "intensity";

interface AxisValueChipProps {
  axis: ChipAxis;
  value: string;
}

export function AxisValueChip({ axis, value }: AxisValueChipProps) {
  const [lang] = useLang();
  const label = axisLabel(value, lang);

  if (axis === "intensity") {
    const level = intensityLevel(value);
    return (
      <span
        className={`${styles.chip} ${styles.intensity}`}
        style={{ background: level ? INTENSITY_COLORS[level] : undefined }}
      >
        {label}
      </span>
    );
  }

  if (axis === "channel") {
    return (
      <span
        className={`${styles.chip} ${styles.channel}`}
        style={{ borderStyle: CHANNEL_BORDER_STYLE[value] ?? "dashed" }}
      >
        {label}
      </span>
    );
  }

  if (axis === "action") {
    return (
      <span className={`${styles.chip} ${styles.action}`}>
        <span className={styles.icon}>{ACTION_FORM_ICONS[value] ?? ""}</span>
        {label}
      </span>
    );
  }

  return <span className={`${styles.chip} ${styles.theme}`}>{label}</span>;
}

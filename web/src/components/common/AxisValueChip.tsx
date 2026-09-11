import { useLang } from "../../hooks/useLang";
import { axisLabel } from "../../i18n";
import { ACTION_FORM_ICONS } from "../../i18n/actionFormIcons";
import styles from "./AxisValueChip.module.css";

export type ChipAxis = "action" | "theme" | "channel" | "intensity";

interface AxisValueChipProps {
  axis: ChipAxis;
  value: string;
}

/** Reference-display chip (About / onboarding / legend). Shares the uniform
 * qualitative pill palette with AxisTag; action chips keep a leading glyph
 * because it doubles as a legend key. */
export function AxisValueChip({ axis, value }: AxisValueChipProps) {
  const [lang] = useLang();
  const label = axisLabel(value, lang);

  if (axis === "action") {
    return (
      <span className={`${styles.chip} ${styles.action}`}>
        <span className={styles.icon}>{ACTION_FORM_ICONS[value] ?? ""}</span>
        {label}
      </span>
    );
  }

  return <span className={`${styles.chip} ${styles[axis]}`}>{label}</span>;
}

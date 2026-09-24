import { useLang } from "../../hooks/useLang";
import { axisLabel } from "../../i18n";
import { ACTION_FORM_ICONS } from "../../i18n/actionFormIcons";
import styles from "./AxisValueChip.module.css";

export type ChipAxis = "action" | "theme" | "channel" | "intensity";

interface AxisValueChipProps {
  axis: ChipAxis;
  value: string;
  /** When provided, the chip becomes a toggle button (used by the legend). */
  onToggle?: () => void;
  /** Emphasize (thicker border) when this value is an active filter. */
  active?: boolean;
}

/** Reference-display chip (About / onboarding / legend). Shares the uniform
 * qualitative pill palette with AxisTag; action chips keep a leading glyph
 * because it doubles as a legend key. */
export function AxisValueChip({ axis, value, onToggle, active }: AxisValueChipProps) {
  const [lang] = useLang();
  const label = axisLabel(value, lang);
  const className = `${styles.chip} ${styles[axis]}${active ? ` ${styles.active}` : ""}`;
  const inner =
    axis === "action" ? (
      <>
        <span className={styles.icon}>{ACTION_FORM_ICONS[value] ?? ""}</span>
        {label}
      </>
    ) : (
      label
    );

  if (onToggle) {
    return (
      <button
        type="button"
        className={`${className} ${styles.interactive}`}
        onClick={onToggle}
        aria-pressed={active ?? false}
      >
        {inner}
      </button>
    );
  }
  return <span className={className}>{inner}</span>;
}

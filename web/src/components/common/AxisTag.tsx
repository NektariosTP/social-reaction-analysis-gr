import { useLang } from "../../hooks/useLang";
import { axisLabel } from "../../i18n";
import styles from "./AxisTag.module.css";

export type AxisTagVariant = "action" | "theme" | "channel" | "intensity";

interface AxisTagProps {
  value: string;
  variant: AxisTagVariant;
}

/**
 * One uniform pill treatment across all four axes — a soft-tinted background
 * with a saturated same-hue label. Axes are told apart by colour alone (a
 * qualitative palette), not by per-axis shape/border/dots.
 */
export function AxisTag({ value, variant }: AxisTagProps) {
  const [lang] = useLang();
  return (
    <span className={`${styles.tag} ${styles[variant]}`}>{axisLabel(value, lang)}</span>
  );
}

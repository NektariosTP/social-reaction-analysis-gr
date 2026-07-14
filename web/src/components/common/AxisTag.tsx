import { useLang } from "../../hooks/useLang";
import { axisLabel } from "../../i18n";
import styles from "./AxisTag.module.css";

export type AxisTagVariant = "action" | "theme" | "channel";

interface AxisTagProps {
  value: string;
  variant: AxisTagVariant;
}

/**
 * Visual encoding kept from the wireframes: solid = Action Form (axis 1),
 * outline = Thematic Field (axis 2), dashed = Channel (axis 3).
 */
export function AxisTag({ value, variant }: AxisTagProps) {
  const [lang] = useLang();
  return <span className={`${styles.tag} ${styles[variant]}`}>{axisLabel(value, lang)}</span>;
}

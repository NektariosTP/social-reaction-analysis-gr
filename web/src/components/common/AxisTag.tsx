import { useLang } from "../../hooks/useLang";
import { axisLabel } from "../../i18n";
import { CHANNEL_BORDER_STYLE } from "../../i18n/taxonomy";
import styles from "./AxisTag.module.css";

export type AxisTagVariant = "action" | "theme" | "channel";

interface AxisTagProps {
  value: string;
  variant: AxisTagVariant;
}

/**
 * Visual encoding kept from the wireframes: solid fill = Action Form (axis 1),
 * outline = Thematic Field (axis 2), border-style-per-value = Channel (axis 3),
 * matching the same encoding used on map markers.
 */
export function AxisTag({ value, variant }: AxisTagProps) {
  const [lang] = useLang();
  const style =
    variant === "channel" ? { borderStyle: CHANNEL_BORDER_STYLE[value] ?? "dashed" } : undefined;
  return (
    <span className={`${styles.tag} ${styles[variant]}`} style={style}>
      {axisLabel(value, lang)}
    </span>
  );
}

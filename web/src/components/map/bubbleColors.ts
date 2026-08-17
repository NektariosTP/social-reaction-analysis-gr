import { intensityLevel } from "../../i18n";

/** Kept in sync with --color-axis4-low/mid/high in styles/tokens.css. */
export const INTENSITY_COLORS: Record<1 | 2 | 3, string> = {
  1: "#4f9d5c",
  2: "#d99a2b",
  3: "#c23b3b",
};
export const INTENSITY_COLOR_NEUTRAL = "#63666e";

/** Resolve an event's intensity string to its marker colour (neutral fallback). */
export function intensityColor(intensity?: string | null): string {
  const level = intensityLevel(intensity);
  return level ? INTENSITY_COLORS[level] : INTENSITY_COLOR_NEUTRAL;
}

import { intensityLevel } from "../../i18n";
import { CHANNEL_BORDER_STYLE } from "../../i18n/taxonomy";
import { actionFormIcon } from "../../i18n/actionFormIcons";
import { INTENSITY_COLORS, INTENSITY_COLOR_NEUTRAL } from "./bubbleColors";

export const MARKER_DIAMETER = 34;

export interface MarkerStyle {
  size: number;
  fill: string;
  borderStyle: "solid" | "dashed" | "dotted";
  icon: string;
}

export interface MarkerProperties {
  intensity?: string | null;
  channel?: string | null;
  action_forms: string[];
}

export function markerStyle(properties: MarkerProperties): MarkerStyle {
  const level = intensityLevel(properties.intensity);
  return {
    size: MARKER_DIAMETER,
    fill: level ? INTENSITY_COLORS[level] : INTENSITY_COLOR_NEUTRAL,
    borderStyle: (properties.channel && CHANNEL_BORDER_STYLE[properties.channel]) || "dashed",
    icon: actionFormIcon(properties.action_forms),
  };
}

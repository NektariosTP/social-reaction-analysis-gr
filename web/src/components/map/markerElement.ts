import { markerStyle, type MarkerProperties } from "./markerStyle";
import styles from "./MapView.module.css";

export function createMarkerElement(
  properties: MarkerProperties,
  articleCount: number,
  selected: boolean,
): HTMLDivElement {
  const style = markerStyle(properties);
  const el = document.createElement("div");
  el.className = styles.bubble;
  el.style.width = `${style.size}px`;
  el.style.height = `${style.size}px`;
  el.style.background = style.fill;
  el.style.borderStyle = style.borderStyle;
  el.textContent = `${style.icon} ${articleCount}`;
  if (selected) {
    el.style.outline = "2px solid var(--color-accent)";
    el.style.outlineOffset = "2px";
  }
  return el;
}

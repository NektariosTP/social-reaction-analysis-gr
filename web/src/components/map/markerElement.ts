import { markerStyle, MARKER_DIAMETER, type MarkerProperties } from "./markerStyle";
import { INTENSITY_COLOR_NEUTRAL } from "./bubbleColors";
import styles from "./MapView.module.css";

export function createMarkerElement(
  properties: MarkerProperties,
  articleCount: number,
  selected: boolean,
): HTMLDivElement {
  const style = markerStyle(properties);

  const wrapper = document.createElement("div");
  wrapper.className = styles.markerWrapper;
  wrapper.style.width = `${style.size}px`;
  wrapper.style.height = `${style.size}px`;
  if (selected) {
    wrapper.style.outline = "2px solid var(--color-accent)";
    wrapper.style.outlineOffset = "2px";
  }

  const bubble = document.createElement("div");
  bubble.className = styles.bubble;
  bubble.dataset.role = "bubble";
  bubble.style.width = "100%";
  bubble.style.height = "100%";
  bubble.style.background = style.fill;
  bubble.style.borderStyle = style.borderStyle;
  bubble.textContent = style.icon;
  wrapper.appendChild(bubble);

  const badge = document.createElement("div");
  badge.className = styles.countBadge;
  badge.dataset.role = "count-badge";
  badge.textContent = String(articleCount);
  wrapper.appendChild(badge);

  return wrapper;
}

export function createClusterMarkerElement(pointCount: number): HTMLDivElement {
  const el = document.createElement("div");
  el.className = styles.bubble;
  el.style.width = `${MARKER_DIAMETER}px`;
  el.style.height = `${MARKER_DIAMETER}px`;
  el.style.background = INTENSITY_COLOR_NEUTRAL;
  el.style.borderStyle = "solid";
  el.textContent = String(pointCount);
  return el;
}

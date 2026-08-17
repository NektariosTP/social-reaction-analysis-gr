import { markerStyle, MARKER_DIAMETER, type MarkerProperties } from "./markerStyle";
import { INTENSITY_COLOR_NEUTRAL } from "./bubbleColors";
import type { GeoJsonFeature } from "../../client/types.gen";
import type { ClusterPreview } from "./clusterPreview";
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

const ORBITER_MAX_DIAMETER = 22;
const ORBITER_MIN_DIAMETER = 14;
const ORBIT_GAP = 4;

function orbiterCircle(feature: GeoJsonFeature, size: number): HTMLDivElement {
  const style = markerStyle(feature.properties);
  const dot = document.createElement("div");
  dot.dataset.role = "orbiter";
  dot.dataset.color = style.fill; // jsdom normalizes inline colors to rgb(); expose the source for tests
  dot.style.position = "absolute";
  dot.style.width = `${size}px`;
  dot.style.height = `${size}px`;
  dot.style.borderRadius = "50%";
  dot.style.background = style.fill;
  dot.style.borderStyle = style.borderStyle;
  dot.style.borderWidth = "1.5px";
  dot.style.borderColor = "var(--color-surface, #fff)";
  dot.style.boxSizing = "border-box";
  dot.style.display = "flex";
  dot.style.alignItems = "center";
  dot.style.justifyContent = "center";
  dot.style.fontSize = `${Math.round(size * 0.55)}px`;
  dot.style.pointerEvents = "auto";
  dot.textContent = style.icon;
  return dot;
}

function remainderPill(count: number, size: number): HTMLDivElement {
  const pill = document.createElement("div");
  pill.dataset.role = "remainder-pill";
  pill.style.position = "absolute";
  pill.style.width = `${size}px`;
  pill.style.height = `${size}px`;
  pill.style.display = "flex";
  pill.style.alignItems = "center";
  pill.style.justifyContent = "center";
  pill.style.borderRadius = "50%";
  pill.style.background = INTENSITY_COLOR_NEUTRAL;
  pill.style.color = "#fff";
  pill.style.fontSize = "9px";
  pill.style.fontWeight = "600";
  pill.style.pointerEvents = "auto";
  pill.textContent = `+${count}`;
  return pill;
}

/** Place `child` on the orbit ring at slot `index` of `ringSlots`, starting from the top (-90°). */
function placeOnRing(
  child: HTMLElement,
  index: number,
  ringSlots: number,
  wrapperDiameter: number,
  orbitRadius: number,
): HTMLElement {
  const angle = ((360 / ringSlots) * index - 90) * (Math.PI / 180);
  const cx = wrapperDiameter / 2 + orbitRadius * Math.cos(angle);
  const cy = wrapperDiameter / 2 + orbitRadius * Math.sin(angle);
  const size = parseFloat(child.style.width);
  child.style.left = `${cx - size / 2}px`;
  child.style.top = `${cy - size / 2}px`;
  return child;
}

export function createClusterMarkerElement(preview: ClusterPreview): HTMLDivElement {
  const centerRadius = MARKER_DIAMETER / 2;
  const orbitRadius = centerRadius + ORBITER_MAX_DIAMETER / 2 + ORBIT_GAP;
  const wrapperDiameter = (orbitRadius + ORBITER_MAX_DIAMETER / 2) * 2;

  const wrapper = document.createElement("div");
  wrapper.style.position = "absolute";
  wrapper.style.width = `${wrapperDiameter}px`;
  wrapper.style.height = `${wrapperDiameter}px`;
  wrapper.style.pointerEvents = "none";

  const center = createMarkerElement(
    preview.center.properties,
    preview.center.properties.article_count,
    false,
  );
  center.style.position = "absolute";
  center.style.left = `${wrapperDiameter / 2 - centerRadius}px`;
  center.style.top = `${wrapperDiameter / 2 - centerRadius}px`;
  center.style.pointerEvents = "auto";
  wrapper.appendChild(center);

  const ringSlots = preview.orbiters.length + (preview.remainderCount > 0 ? 1 : 0);
  preview.orbiters.forEach((orbiter, i) => {
    const size =
      ringSlots <= 1
        ? ORBITER_MAX_DIAMETER
        : ORBITER_MAX_DIAMETER -
          (i / (ringSlots - 1)) * (ORBITER_MAX_DIAMETER - ORBITER_MIN_DIAMETER);
    wrapper.appendChild(
      placeOnRing(orbiterCircle(orbiter, size), i, ringSlots, wrapperDiameter, orbitRadius),
    );
  });
  if (preview.remainderCount > 0) {
    wrapper.appendChild(
      placeOnRing(
        remainderPill(preview.remainderCount, ORBITER_MIN_DIAMETER),
        preview.orbiters.length,
        ringSlots,
        wrapperDiameter,
        orbitRadius,
      ),
    );
  }

  return wrapper;
}

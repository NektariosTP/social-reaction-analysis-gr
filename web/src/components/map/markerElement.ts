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
  dot.classList.add(styles.orbiterDrift);
  dot.style.animationDelay = driftDelay(feature.properties.id);
  return dot;
}

/** Deterministic small delay (0.0-1.9s) from a feature id, so orbiters in one cluster don't drift in lockstep. */
function driftDelay(id: string): string {
  let sum = 0;
  for (let i = 0; i < id.length; i++) sum += id.charCodeAt(i);
  return `${(sum % 20) / 10}s`;
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

/** Place `child` on the orbit ring at slot `index` of `ringSlots`, starting from the top (-90°).
 * When `animateEntrance` is true, `child` starts collapsed at the wrapper's center point and
 * transitions out to its ring position on the next frame (CSS `.orbiterEnter` transition). */
function placeOnRing(
  child: HTMLElement,
  index: number,
  ringSlots: number,
  wrapperDiameter: number,
  orbitRadius: number,
  animateEntrance: boolean,
): HTMLElement {
  const angle = ((360 / ringSlots) * index - 90) * (Math.PI / 180);
  const size = parseFloat(child.style.width);
  const finalLeft = wrapperDiameter / 2 + orbitRadius * Math.cos(angle) - size / 2;
  const finalTop = wrapperDiameter / 2 + orbitRadius * Math.sin(angle) - size / 2;

  if (animateEntrance) {
    const centerLeft = wrapperDiameter / 2 - size / 2;
    const centerTop = wrapperDiameter / 2 - size / 2;
    child.classList.add(styles.orbiterEnter);
    child.style.left = `${centerLeft}px`;
    child.style.top = `${centerTop}px`;
    child.style.opacity = "0";
    requestAnimationFrame(() => {
      child.style.left = `${finalLeft}px`;
      child.style.top = `${finalTop}px`;
      child.style.opacity = "1";
    });
  } else {
    child.style.left = `${finalLeft}px`;
    child.style.top = `${finalTop}px`;
  }
  return child;
}

export function createClusterMarkerElement(
  preview: ClusterPreview,
  animateEntrance: boolean = false,
): HTMLDivElement {
  const centerRadius = MARKER_DIAMETER / 2;
  const orbitRadius = centerRadius + ORBITER_MAX_DIAMETER / 2 + ORBIT_GAP;
  const wrapperDiameter = (orbitRadius + ORBITER_MAX_DIAMETER / 2) * 2;

  const wrapper = document.createElement("div");
  wrapper.style.position = "absolute";
  wrapper.style.width = `${wrapperDiameter}px`;
  wrapper.style.height = `${wrapperDiameter}px`;
  wrapper.style.pointerEvents = "none";
  wrapper.dataset.role = "cluster-wrapper";

  // maplibre-gl owns `wrapper`'s inline `transform` (it re-writes translate()
  // every frame to keep the marker geo-anchored). The zoom "pulse" animation
  // must therefore live on an inner element it never touches — animating the
  // wrapper's own transform clobbers that translate mid-zoom (the cluster
  // jumped to the map's top-left corner / drifted). This inner box fills the
  // wrapper, so the children's left/top math is unchanged, and it pulses
  // symmetrically around its own centre (= the geo anchor).
  const pulse = document.createElement("div");
  pulse.style.position = "absolute";
  pulse.style.inset = "0";
  pulse.dataset.role = "cluster-pulse";

  const center = createMarkerElement(
    preview.center.properties,
    preview.center.properties.article_count,
    false,
  );
  center.style.position = "absolute";
  center.style.left = `${wrapperDiameter / 2 - centerRadius}px`;
  center.style.top = `${wrapperDiameter / 2 - centerRadius}px`;
  center.style.pointerEvents = "auto";
  pulse.appendChild(center);

  const ringSlots = preview.orbiters.length + (preview.remainderCount > 0 ? 1 : 0);
  preview.orbiters.forEach((orbiter, i) => {
    const size =
      ringSlots <= 1
        ? ORBITER_MAX_DIAMETER
        : ORBITER_MAX_DIAMETER -
          (i / (ringSlots - 1)) * (ORBITER_MAX_DIAMETER - ORBITER_MIN_DIAMETER);
    pulse.appendChild(
      placeOnRing(
        orbiterCircle(orbiter, size),
        i,
        ringSlots,
        wrapperDiameter,
        orbitRadius,
        animateEntrance,
      ),
    );
  });
  if (preview.remainderCount > 0) {
    pulse.appendChild(
      placeOnRing(
        remainderPill(preview.remainderCount, ORBITER_MIN_DIAMETER),
        preview.orbiters.length,
        ringSlots,
        wrapperDiameter,
        orbitRadius,
        animateEntrance,
      ),
    );
  }

  wrapper.appendChild(pulse);
  return wrapper;
}

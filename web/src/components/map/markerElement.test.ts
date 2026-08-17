import { describe, expect, it } from "vitest";
import { createMarkerElement, createClusterMarkerElement } from "./markerElement";
import { intensityColor } from "./bubbleColors";
import type { GeoJsonFeature } from "../../client/types.gen";
import type { ClusterPreview } from "./clusterPreview";

describe("createMarkerElement", () => {
  it("renders only the action-form icon in the main bubble", () => {
    const el = createMarkerElement(
      { intensity: "Ειρηνική", channel: "Φυσικό (offline)", action_forms: ["Κατάληψη"] },
      12,
      false,
    );
    const bubble = el.querySelector<HTMLElement>('[data-role="bubble"]');
    expect(bubble?.textContent).toBe("🏛");
  });

  it("renders the article count in a separate badge, not in the main bubble", () => {
    const el = createMarkerElement({ intensity: null, channel: null, action_forms: [] }, 7, false);
    const badge = el.querySelector<HTMLElement>('[data-role="count-badge"]');
    expect(badge?.textContent).toBe("7");
  });

  it("renders 2-digit counts in the badge without adding them to the bubble", () => {
    const el = createMarkerElement({ intensity: null, channel: null, action_forms: [] }, 42, false);
    const badge = el.querySelector<HTMLElement>('[data-role="count-badge"]');
    const bubble = el.querySelector<HTMLElement>('[data-role="bubble"]');
    expect(badge?.textContent).toBe("42");
    expect(bubble?.textContent).not.toContain("4");
  });

  it("applies the fixed diameter to the wrapper regardless of article count", () => {
    const el = createMarkerElement({ intensity: null, channel: null, action_forms: [] }, 500, false);
    expect(el.style.width).toBe("34px");
    expect(el.style.height).toBe("34px");
  });

  it("shows an accent outline on the wrapper when selected", () => {
    const el = createMarkerElement({ intensity: null, channel: null, action_forms: [] }, 1, true);
    expect(el.style.outline).toContain("2px");
  });

  it("shows no outline when not selected", () => {
    const el = createMarkerElement({ intensity: null, channel: null, action_forms: [] }, 1, false);
    expect(el.style.outline).toBe("");
  });
});

function leaf(
  id: string,
  intensity: string | null,
  extra: { action_forms?: string[]; channel?: string | null } = {},
): GeoJsonFeature {
  return {
    geometry: { coordinates: [23.7, 38.0] },
    properties: {
      id,
      action_forms: extra.action_forms ?? [],
      thematic_fields: [],
      channel: extra.channel ?? null,
      intensity,
      article_count: 1,
    },
  };
}

describe("createClusterMarkerElement", () => {
  it("makes the wrapper non-interactive so only its children hit-test", () => {
    const preview: ClusterPreview = {
      center: leaf("c", "Βίαιη/Συγκρουσιακή"),
      orbiters: [leaf("o1", "Ειρηνική")],
      remainderCount: 0,
    };
    const el = createClusterMarkerElement(preview);
    expect(el.style.pointerEvents).toBe("none");
    expect(el.style.position).toBe("absolute");
  });

  it("renders the center plus one child per orbiter and no pill when no remainder", () => {
    const preview: ClusterPreview = {
      center: leaf("c", null),
      orbiters: [leaf("o1", "Ειρηνική"), leaf("o2", "Βίαιη/Συγκρουσιακή")],
      remainderCount: 0,
    };
    const el = createClusterMarkerElement(preview);
    expect(el.children).toHaveLength(3); // center + 2 orbiters
    expect(el.querySelector('[data-role="remainder-pill"]')).toBeNull();
  });

  it("colors each orbiter by its own intensity", () => {
    const orbiter = leaf("o1", "Ειρηνική");
    const preview: ClusterPreview = { center: leaf("c", null), orbiters: [orbiter], remainderCount: 0 };
    const el = createClusterMarkerElement(preview);
    const dot = el.querySelector<HTMLElement>('[data-role="orbiter"]');
    expect(dot?.dataset.color).toBe(intensityColor("Ειρηνική"));
  });

  it("adds a +N pill only when remainderCount > 0", () => {
    const preview: ClusterPreview = {
      center: leaf("c", null),
      orbiters: [leaf("o1", null)],
      remainderCount: 7,
    };
    const el = createClusterMarkerElement(preview);
    const pill = el.querySelector<HTMLElement>('[data-role="remainder-pill"]');
    expect(pill?.textContent).toBe("+7");
    expect(el.children).toHaveLength(3); // center + 1 orbiter + pill
  });

  it("shows the orbiter's own action-form emoji and channel border style", () => {
    const orbiter = leaf("o1", "Ειρηνική", {
      action_forms: ["Κατάληψη"],
      channel: "Φυσικό (offline)",
    });
    const preview: ClusterPreview = { center: leaf("c", null), orbiters: [orbiter], remainderCount: 0 };
    const el = createClusterMarkerElement(preview);
    const dot = el.querySelector<HTMLElement>('[data-role="orbiter"]');
    expect(dot?.textContent).toBe("🏛");
    expect(dot?.style.borderStyle).toBe("solid");
  });
});

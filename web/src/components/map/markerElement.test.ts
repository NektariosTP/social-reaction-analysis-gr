import { describe, expect, it } from "vitest";
import { createMarkerElement, createClusterMarkerElement } from "./markerElement";

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

describe("createClusterMarkerElement", () => {
  it("renders the cluster point count as marker text", () => {
    const el = createClusterMarkerElement(3);
    expect(el.textContent).toBe("3");
  });

  it("applies the same fixed diameter as an individual marker", () => {
    const el = createClusterMarkerElement(3);
    expect(el.style.width).toBe("34px");
    expect(el.style.height).toBe("34px");
  });

  it("uses a solid border and neutral fill (no single intensity applies)", () => {
    const el = createClusterMarkerElement(3);
    expect(el.style.borderStyle).toBe("solid");
    expect(el.style.background).toBe("rgb(99, 102, 110)");
  });
});

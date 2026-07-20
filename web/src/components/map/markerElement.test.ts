import { describe, expect, it } from "vitest";
import { createMarkerElement } from "./markerElement";

describe("createMarkerElement", () => {
  it("renders the action-form icon and article count as marker text", () => {
    const el = createMarkerElement(
      { intensity: "Ειρηνική", channel: "Φυσικό (offline)", action_forms: ["Κατάληψη"] },
      12,
      false,
    );
    expect(el.textContent).toBe("🏛 12");
  });

  it("applies the fixed diameter regardless of article count", () => {
    const el = createMarkerElement({ intensity: null, channel: null, action_forms: [] }, 500, false);
    expect(el.style.width).toBe("34px");
    expect(el.style.height).toBe("34px");
  });

  it("shows an accent outline when selected", () => {
    const el = createMarkerElement({ intensity: null, channel: null, action_forms: [] }, 1, true);
    expect(el.style.outline).toContain("2px");
  });

  it("shows no outline when not selected", () => {
    const el = createMarkerElement({ intensity: null, channel: null, action_forms: [] }, 1, false);
    expect(el.style.outline).toBe("");
  });
});

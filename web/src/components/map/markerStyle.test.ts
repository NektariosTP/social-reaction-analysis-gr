import { describe, expect, it } from "vitest";
import { markerStyle, MARKER_DIAMETER } from "./markerStyle";

describe("markerStyle", () => {
  it("always returns the fixed marker diameter regardless of article count", () => {
    const style = markerStyle({ intensity: "Ειρηνική", channel: "Φυσικό (offline)", action_forms: [] });
    expect(style.size).toBe(MARKER_DIAMETER);
  });

  it("maps intensity level to the matching fill color", () => {
    const style = markerStyle({ intensity: "Βίαιη/Συγκρουσιακή", channel: null, action_forms: [] });
    expect(style.fill).toBe("#c23b3b");
  });

  it("falls back to the neutral fill when intensity is missing", () => {
    const style = markerStyle({ intensity: null, channel: null, action_forms: [] });
    expect(style.fill).toBe("#63666e");
  });

  it("maps channel value to the matching border style", () => {
    const style = markerStyle({ intensity: null, channel: "Ψηφιακό (online)", action_forms: [] });
    expect(style.borderStyle).toBe("dotted");
  });

  it("uses the primary action form's icon", () => {
    const style = markerStyle({ intensity: null, channel: null, action_forms: ["Κατάληψη"] });
    expect(style.icon).toBe("🏛");
  });
});

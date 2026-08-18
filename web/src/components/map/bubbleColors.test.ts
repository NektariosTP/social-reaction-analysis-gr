import { describe, expect, it } from "vitest";
import { intensityColor, INTENSITY_COLORS, INTENSITY_COLOR_NEUTRAL } from "./bubbleColors";

describe("intensityColor", () => {
  it("maps a peaceful intensity to the level-1 colour", () => {
    expect(intensityColor("Ειρηνική")).toBe(INTENSITY_COLORS[1]);
  });

  it("maps a violent intensity to the level-3 colour", () => {
    expect(intensityColor("Βίαιη/Συγκρουσιακή")).toBe(INTENSITY_COLORS[3]);
  });

  it("falls back to neutral for null/unknown", () => {
    expect(intensityColor(null)).toBe(INTENSITY_COLOR_NEUTRAL);
    expect(intensityColor("nonsense")).toBe(INTENSITY_COLOR_NEUTRAL);
  });
});

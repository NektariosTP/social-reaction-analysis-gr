import { describe, expect, it } from "vitest";
import { actionFormIcon, ACTION_FORM_ICON_FALLBACK } from "./actionFormIcons";

describe("actionFormIcon", () => {
  it("returns the icon for the first action form in the array", () => {
    expect(actionFormIcon(["Απεργία/Στάση εργασίας", "Κατάληψη"])).toBe("✊");
  });

  it("falls back to the generic icon for an empty array", () => {
    expect(actionFormIcon([])).toBe(ACTION_FORM_ICON_FALLBACK);
  });

  it("falls back to the generic icon for null or undefined", () => {
    expect(actionFormIcon(null)).toBe(ACTION_FORM_ICON_FALLBACK);
    expect(actionFormIcon(undefined)).toBe(ACTION_FORM_ICON_FALLBACK);
  });

  it("falls back to the generic icon for an unrecognized value", () => {
    expect(actionFormIcon(["not-a-real-value"])).toBe(ACTION_FORM_ICON_FALLBACK);
  });
});

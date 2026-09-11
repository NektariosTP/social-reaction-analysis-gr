import { describe, expect, it } from "vitest";
import i18n from "./index";

describe("i18n defaults", () => {
  it("falls back to Greek and only detects from localStorage", () => {
    // fallbackLng normalizes to ["el"] internally
    expect(i18n.options.fallbackLng).toEqual(["el"]);
    expect(i18n.options.detection?.order).toEqual(["localStorage"]);
  });
});

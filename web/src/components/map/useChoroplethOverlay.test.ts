import { describe, it, expect } from "vitest";
import { buildChoroplethExpression } from "./useChoroplethOverlay";

describe("buildChoroplethExpression", () => {
  it("maps region_code to a match expression with a fallback", () => {
    const expr = buildChoroplethExpression([
      { region_code: "Attica", value: 10, period: "2023" },
      { region_code: "Crete", value: 20, period: "2023" },
    ]);
    // ["match", ["get","region_code"], "Attica", <color>, "Crete", <color>, <fallback>]
    expect(Array.isArray(expr)).toBe(true);
    if (!Array.isArray(expr)) throw new Error("expected array");
    expect(expr[0]).toBe("match");
    expect(expr).toContain("Attica");
    expect(expr).toContain("Crete");
    expect(expr[expr.length - 1]).toBe("#cccccc"); // no-data fallback
  });

  it("returns a flat fallback fill when there are no values", () => {
    expect(buildChoroplethExpression([])).toEqual("#cccccc");
  });
});

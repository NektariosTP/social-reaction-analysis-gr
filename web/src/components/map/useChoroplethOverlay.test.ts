import { describe, it, expect } from "vitest";
import {
  buildChoroplethExpression,
  buildLabelExpression,
  buildLabelPoints,
  formatChoroplethValue,
} from "./useChoroplethOverlay";

const NO_DATA = "#cccccc";

describe("buildChoroplethExpression (rank-normalized)", () => {
  it("returns a single NO_DATA color when there are no values", () => {
    expect(buildChoroplethExpression([])).toBe(NO_DATA);
    expect(buildChoroplethExpression([{ region_code: "Attica", value: null }])).toBe(NO_DATA);
  });

  it("assigns distinct colors by rank for distinct values", () => {
    const expr = buildChoroplethExpression([
      { region_code: "A", value: 1 },
      { region_code: "B", value: 5 },
      { region_code: "C", value: 9 },
    ]) as unknown[];
    // ["match", ["get","region_code"], "A", cA, "B", cB, "C", cC, NO_DATA]
    const cA = expr[3], cB = expr[5], cC = expr[7];
    expect(cA).not.toBe(cB);
    expect(cB).not.toBe(cC);
    expect(expr[expr.length - 1]).toBe(NO_DATA);
  });

  it("does not flatten the field when one value is a large outlier", () => {
    // rank spacing is even regardless of magnitude skew
    const expr = buildChoroplethExpression([
      { region_code: "A", value: 1 },
      { region_code: "B", value: 2 },
      { region_code: "C", value: 1000 },
    ]) as unknown[];
    expect(expr[3]).not.toBe(expr[5]); // A vs B still differ
  });
});

describe("buildLabelExpression", () => {
  it("maps region_code to a formatted value string", () => {
    const expr = buildLabelExpression([{ region_code: "Attica", value: 10.5 }]) as unknown[];
    expect(expr[0]).toBe("match");
    expect(expr).toContain("Attica");
    expect(expr).toContain("10.5");
  });
});

describe("buildLabelPoints", () => {
  it("produces exactly one Point feature per periphery with a value, regardless of island count", () => {
    // South Aegean/Ionian Islands/Attica boundaries are MultiPolygons with dozens
    // of disjoint island parts; labels must not be placed once per island.
    const fc = buildLabelPoints([
      { region_code: "Attica", value: 10.5 },
      { region_code: "South Aegean", value: 8.1 },
    ]);
    expect(fc.features).toHaveLength(2);
    expect(fc.features.every((f) => f.geometry.type === "Point")).toBe(true);
    expect(fc.features.map((f) => f.properties?.region_code).sort()).toEqual([
      "Attica",
      "South Aegean",
    ]);
  });

  it("excludes peripheries with no value and unknown region codes", () => {
    const fc = buildLabelPoints([
      { region_code: "Attica", value: null },
      { region_code: "Not A Real Region", value: 5 },
    ]);
    expect(fc.features).toHaveLength(0);
  });
});

describe("formatChoroplethValue", () => {
  it("keeps at most one decimal and appends % only for percent units", () => {
    expect(formatChoroplethValue(10.53, "%")).toBe("10.5%");
    expect(formatChoroplethValue(20000, "EUR")).toBe("20,000");
  });
});

import { describe, expect, it } from "vitest";
import { estimateLabelBox, selectVisibleLabels, type LabelBox } from "./labelPlacement";

const box = (id: string, x: number, y: number, priority = 0): LabelBox => ({
  id,
  x,
  y,
  width: 100,
  height: 30,
  priority,
});

describe("selectVisibleLabels", () => {
  it("keeps all labels when none overlap", () => {
    const boxes = [box("a", 0, 0), box("b", 500, 0), box("c", 0, 500)];
    expect(selectVisibleLabels(boxes)).toEqual(new Set(["a", "b", "c"]));
  });

  it("drops a lower-priority label that overlaps a higher-priority one", () => {
    // b sits right on top of a (same spot); a has higher priority so it wins.
    const boxes = [box("a", 100, 100, 5), box("b", 110, 105, 1)];
    expect(selectVisibleLabels(boxes)).toEqual(new Set(["a"]));
  });

  it("never suppresses the selected (highest-priority) label", () => {
    // The selected marker is fed first with the top priority even if listed later.
    const boxes = [box("other", 100, 100, 0), box("selected", 110, 105, 100)];
    expect(selectVisibleLabels(boxes)).toEqual(new Set(["selected"]));
  });

  it("allows a label that only overlaps horizontally but not vertically", () => {
    const boxes = [box("a", 100, 0), box("b", 100, 200)];
    expect(selectVisibleLabels(boxes)).toEqual(new Set(["a", "b"]));
  });

  it("allows a label that only overlaps vertically but not horizontally", () => {
    const boxes = [box("a", 0, 100), box("b", 300, 105)];
    expect(selectVisibleLabels(boxes)).toEqual(new Set(["a", "b"]));
  });
});

describe("estimateLabelBox", () => {
  it("centres the box on the point and drops it below by the offset", () => {
    const b = estimateLabelBox("id", "Αθήνα", { x: 200, y: 100 }, 17, 0);
    expect(b.id).toBe("id");
    expect(b.x).toBe(200);
    expect(b.y).toBe(117);
    expect(b.priority).toBe(0);
  });

  it("stays single-line-tall for short text", () => {
    const short = estimateLabelBox("s", "Πάτρα", { x: 0, y: 0 }, 0, 0);
    expect(short.width).toBeLessThan(170);
    expect(short.height).toBe(18); // 1 line * 12 + 6 padding
  });

  it("clamps width and grows to two lines for long text", () => {
    const long = estimateLabelBox(
      "l",
      "Θεσσαλονίκη Κέντρο Λευκός Πύργος και γύρω περιοχή",
      { x: 0, y: 0 },
      0,
      0,
    );
    expect(long.width).toBe(170);
    expect(long.height).toBe(30); // 2 lines * 12 + 6 padding
  });
});

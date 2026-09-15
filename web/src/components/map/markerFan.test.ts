import { describe, expect, it } from "vitest";
import { fanOutOffsets, fanOffsetsByCoincidence } from "./markerFan";

describe("fanOutOffsets", () => {
  it("leaves a single marker on the point", () => {
    expect(fanOutOffsets(1, 3, 40)).toEqual([[0, 0]]);
  });

  it("spreads two markers symmetrically in one row", () => {
    expect(fanOutOffsets(2, 3, 40)).toEqual([
      [-20, 0],
      [20, 0],
    ]);
  });

  it("centres a full row of three", () => {
    expect(fanOutOffsets(3, 3, 40)).toEqual([
      [-40, 0],
      [0, 0],
      [40, 0],
    ]);
  });

  it("wraps to a second, centred row past the per-row limit", () => {
    // 4 items, 3 per row → row0 of 3 (above centre), row1 of 1 (below centre).
    expect(fanOutOffsets(4, 3, 40)).toEqual([
      [-40, -20],
      [0, -20],
      [40, -20],
      [0, 20],
    ]);
  });
});

describe("fanOffsetsByCoincidence", () => {
  it("assigns no offset when every marker has unique coordinates", () => {
    const map = fanOffsetsByCoincidence(
      [
        { id: "a", coordinates: [23.7, 38.0] },
        { id: "b", coordinates: [22.9, 40.6] },
      ],
      3,
      40,
    );
    expect(map.size).toBe(0);
  });

  it("fans out only the markers that share exact coordinates", () => {
    const map = fanOffsetsByCoincidence(
      [
        { id: "a", coordinates: [23.7, 38.0] },
        { id: "b", coordinates: [23.7, 38.0] },
        { id: "lonely", coordinates: [22.9, 40.6] },
      ],
      3,
      40,
    );
    expect(map.get("a")).toEqual([-20, 0]);
    expect(map.get("b")).toEqual([20, 0]);
    expect(map.has("lonely")).toBe(false);
  });

  it("keeps each coincident group's offsets in input order", () => {
    const map = fanOffsetsByCoincidence(
      [
        { id: "a", coordinates: [1, 1] },
        { id: "b", coordinates: [1, 1] },
        { id: "c", coordinates: [1, 1] },
      ],
      3,
      40,
    );
    expect([map.get("a"), map.get("b"), map.get("c")]).toEqual([
      [-40, 0],
      [0, 0],
      [40, 0],
    ]);
  });
});

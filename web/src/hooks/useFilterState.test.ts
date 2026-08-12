import { describe, expect, it } from "vitest";
import { toggleWithAllSentinel } from "./useFilterState";

const ALL = ["peaceful", "disruptive", "violent"];

describe("toggleWithAllSentinel", () => {
  it("unchecking one value from the all-selected sentinel keeps the other two selected", () => {
    const next = toggleWithAllSentinel(ALL, [], "disruptive");
    expect(next.sort()).toEqual(["peaceful", "violent"]);
  });

  it("toggles membership normally when a subset is already selected", () => {
    expect(toggleWithAllSentinel(ALL, ["peaceful"], "violent").sort()).toEqual(
      ["peaceful", "violent"],
    );
    expect(toggleWithAllSentinel(ALL, ["peaceful", "violent"], "violent")).toEqual(["peaceful"]);
  });

  it("collapses back to the empty sentinel when every value becomes selected again", () => {
    const next = toggleWithAllSentinel(ALL, ["peaceful", "violent"], "disruptive");
    expect(next).toEqual([]);
  });

  it("unchecking the last selected value returns an empty (non-sentinel-triggering) list", () => {
    expect(toggleWithAllSentinel(ALL, ["peaceful"], "peaceful")).toEqual([]);
  });
});

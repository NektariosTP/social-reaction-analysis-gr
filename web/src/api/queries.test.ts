import { describe, expect, it } from "vitest";
import type { EventSummary } from "../client/types.gen";
import { partitionByNational } from "./queries";

function ev(id: string, is_national: boolean): EventSummary {
  return {
    id,
    is_national,
    action_forms: [],
    thematic_fields: [],
    channel: null,
    intensity: null,
    summary_el: null,
    summary_en: null,
    article_count: 0,
    source_count: 0,
    status: "enriched",
  } as EventSummary;
}

describe("partitionByNational", () => {
  it("splits national from the rest, preserving order", () => {
    const { panhellenic, other } = partitionByNational([
      ev("a", true),
      ev("b", false),
      ev("c", true),
    ]);
    expect(panhellenic.map((e) => e.id)).toEqual(["a", "c"]);
    expect(other.map((e) => e.id)).toEqual(["b"]);
  });

  it("handles all-national and none-national", () => {
    expect(partitionByNational([ev("a", true)]).other).toEqual([]);
    expect(partitionByNational([ev("a", false)]).panhellenic).toEqual([]);
  });
});

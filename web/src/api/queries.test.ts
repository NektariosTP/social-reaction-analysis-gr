import { describe, expect, it } from "vitest";
import type { EventSummary } from "../client/types.gen";
import { applyClientFilters, partitionByNational } from "./queries";

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

describe("applyClientFilters geo scoping", () => {
  const base = { action_forms: [], thematic_fields: [], intensity: null } as const;
  const rows = [
    { ...base, region_code: "Attica", municipality: "Δήμος Αθηναίων" },
    { ...base, region_code: "Crete", municipality: "Δήμος Ηρακλείου" },
    { ...base, region_code: null, municipality: null },
  ];

  it("filters by regionCode", () => {
    expect(applyClientFilters(rows, { regionCode: "Attica" })).toHaveLength(1);
  });

  it("filters by municipality", () => {
    expect(applyClientFilters(rows, { municipality: "Δήμος Ηρακλείου" })).toHaveLength(1);
  });

  it("passes everything through when no geo filter set", () => {
    expect(applyClientFilters(rows, {})).toHaveLength(3);
  });
});

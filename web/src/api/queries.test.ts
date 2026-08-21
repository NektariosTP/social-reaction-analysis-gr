import { describe, expect, it, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createElement, type ReactNode } from "react";
import type { EventSummary } from "../client/types.gen";
import { applyClientFilters, partitionByNational, useRegionIndicators } from "./queries";

vi.mock("../client/sdk.gen", async () => {
  const actual = await vi.importActual<typeof import("../client/sdk.gen")>("../client/sdk.gen");
  return {
    ...actual,
    regionIndicatorsRegionsRegionCodeIndicatorsGet: vi.fn(async () => ({
      data: { region_code: "Attica", always_on: [], thematic: [] },
    })),
  };
});

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
  const base = {
    action_forms: [] as string[],
    thematic_fields: [] as string[],
    intensity: null as string | null,
  };
  const rows = [
    { ...base, region_code: "Attica", municipality: "Δήμος Αθηναίων" },
    { ...base, region_code: "Crete", municipality: "Δήμος Ηρακλείου" },
    { ...base, region_code: null, municipality: null },
  ];

  it("filters by regionCode", () => {
    expect(applyClientFilters(rows, { regionCode: "Attica" })).toHaveLength(1);
  });

  it("matches Greek-coded events when drilling into the English periphery name", () => {
    // Regression: region_code is language-inconsistent in the data, so drilling
    // into "Attica" used to drop events stored as "Αττική".
    const mixed = [
      { action_forms: [], thematic_fields: [], intensity: null, region_code: "Αττική", municipality: null },
      { action_forms: [], thematic_fields: [], intensity: null, region_code: "Attica", municipality: null },
      { action_forms: [], thematic_fields: [], intensity: null, region_code: "Crete", municipality: null },
    ];
    expect(applyClientFilters(mixed, { regionCode: "Attica" })).toHaveLength(2);
  });

  it("filters by municipality", () => {
    expect(applyClientFilters(rows, { municipality: "Δήμος Ηρακλείου" })).toHaveLength(1);
  });

  it("passes everything through when no geo filter set", () => {
    expect(applyClientFilters(rows, {})).toHaveLength(3);
  });
});

function queryWrapper() {
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return ({ children }: { children: ReactNode }) =>
    createElement(QueryClientProvider, { client: queryClient }, children);
}

describe("useRegionIndicators", () => {
  it("resolves the region indicators payload", async () => {
    const { result } = renderHook(() => useRegionIndicators("Attica"), {
      wrapper: queryWrapper(),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.region_code).toBe("Attica");
  });
});

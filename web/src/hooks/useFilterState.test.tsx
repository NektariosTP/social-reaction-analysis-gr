import { describe, expect, it } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { toggleWithAllSentinel, useFilterState } from "./useFilterState";

const ALL = ["peaceful", "disruptive", "violent"];

// Real taxonomy value: contains a literal comma inside the label itself.
const DISRUPTIVE = "Διαταρακτική (μη βίαιη, παρεμποδιστική)";
const PEACEFUL = "Ειρηνική";
const VIOLENT = "Βίαιη/Συγκρουσιακή";

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

  it("unchecking the last selected value produces a distinct 'none selected' marker, not the all-sentinel []", () => {
    const next = toggleWithAllSentinel(ALL, ["peaceful"], "peaceful");
    expect(next).not.toEqual([]);
    // None of the real values should read as selected against this result.
    expect(ALL.some((v) => next.includes(v))).toBe(false);
  });

  it("re-checking a value from the 'none selected' state selects just that value", () => {
    const none = toggleWithAllSentinel(ALL, ["peaceful"], "peaceful");
    const next = toggleWithAllSentinel(ALL, none, "violent");
    expect(next).toEqual(["violent"]);
  });

  it("walking all three down to zero and back up round-trips through all/none correctly", () => {
    let selected: string[] = []; // starts at "all"
    selected = toggleWithAllSentinel(ALL, selected, "peaceful");
    selected = toggleWithAllSentinel(ALL, selected, "violent");
    selected = toggleWithAllSentinel(ALL, selected, "disruptive"); // now zero selected
    expect(ALL.some((v) => selected.includes(v))).toBe(false);

    selected = toggleWithAllSentinel(ALL, selected, "disruptive");
    expect(selected).toEqual(["disruptive"]);
    selected = toggleWithAllSentinel(ALL, selected, "peaceful");
    selected = toggleWithAllSentinel(ALL, selected, "violent");
    expect(selected).toEqual([]); // back to "all"
  });
});

describe("useFilterState URL round-trip", () => {
  it("preserves a value containing a literal comma alongside another value", () => {
    const { result } = renderHook(() => useFilterState(), {
      wrapper: ({ children }) => <MemoryRouter initialEntries={["/"]}>{children}</MemoryRouter>,
    });

    act(() => {
      result.current.setFilters({ intensities: [DISRUPTIVE, VIOLENT] });
    });

    expect(result.current.filters.intensities.sort()).toEqual([DISRUPTIVE, VIOLENT].sort());
  });

  it("round-trips the comma-toggle sequence from the reported bug", () => {
    const { result } = renderHook(() => useFilterState(), {
      wrapper: ({ children }) => <MemoryRouter initialEntries={["/"]}>{children}</MemoryRouter>,
    });

    // Starting from the all-selected sentinel ([]), uncheck "Peaceful".
    act(() => {
      const all = [PEACEFUL, DISRUPTIVE, VIOLENT];
      result.current.setFilters({
        intensities: toggleWithAllSentinel(all, result.current.filters.intensities, PEACEFUL),
      });
    });

    expect(result.current.filters.intensities.sort()).toEqual([DISRUPTIVE, VIOLENT].sort());
  });

  it("persists an explicit zero-selection across the URL instead of snapping back to all", () => {
    const { result } = renderHook(() => useFilterState(), {
      wrapper: ({ children }) => <MemoryRouter initialEntries={["/"]}>{children}</MemoryRouter>,
    });
    const all = [PEACEFUL, DISRUPTIVE, VIOLENT];

    act(() => {
      let selected = result.current.filters.intensities;
      selected = toggleWithAllSentinel(all, selected, PEACEFUL);
      result.current.setFilters({ intensities: selected });
    });
    act(() => {
      let selected = result.current.filters.intensities;
      selected = toggleWithAllSentinel(all, selected, DISRUPTIVE);
      result.current.setFilters({ intensities: selected });
    });
    act(() => {
      let selected = result.current.filters.intensities;
      selected = toggleWithAllSentinel(all, selected, VIOLENT);
      result.current.setFilters({ intensities: selected });
    });

    // Nothing should read as selected — and crucially the state must not have
    // collapsed back to the "all selected" sentinel ([]).
    expect(all.some((v) => result.current.filters.intensities.includes(v))).toBe(false);
    expect(result.current.filters.intensities).not.toEqual([]);
  });
});

describe("useFilterState day (time-travel) param", () => {
  it("defaults day to null (Live) when the `d` param is absent", () => {
    const { result } = renderHook(() => useFilterState(), {
      wrapper: ({ children }) => <MemoryRouter initialEntries={["/"]}>{children}</MemoryRouter>,
    });
    expect(result.current.filters.day).toBeNull();
  });

  it("round-trips a selected day through the `d` URL param", () => {
    const { result } = renderHook(() => useFilterState(), {
      wrapper: ({ children }) => <MemoryRouter initialEntries={["/"]}>{children}</MemoryRouter>,
    });
    act(() => {
      result.current.setFilters({ day: "2026-09-09" });
    });
    expect(result.current.filters.day).toBe("2026-09-09");
  });

  it("reads an initial day from the `d` param", () => {
    const { result } = renderHook(() => useFilterState(), {
      wrapper: ({ children }) => <MemoryRouter initialEntries={["/?d=2026-09-01"]}>{children}</MemoryRouter>,
    });
    expect(result.current.filters.day).toBe("2026-09-01");
  });
});

describe("useFilterState windowDays (range preset)", () => {
  it("defaults windowDays to null when `w` is absent", () => {
    const { result } = renderHook(() => useFilterState(), {
      wrapper: ({ children }) => <MemoryRouter initialEntries={["/"]}>{children}</MemoryRouter>,
    });
    expect(result.current.filters.windowDays).toBeNull();
  });

  it("reads an initial windowDays from the `w` param", () => {
    const { result } = renderHook(() => useFilterState(), {
      wrapper: ({ children }) => <MemoryRouter initialEntries={["/?w=7"]}>{children}</MemoryRouter>,
    });
    expect(result.current.filters.windowDays).toBe(7);
  });

  it("setting windowDays clears an existing exact day (mutually exclusive)", () => {
    const { result } = renderHook(() => useFilterState(), {
      wrapper: ({ children }) => <MemoryRouter initialEntries={["/?d=2026-09-18"]}>{children}</MemoryRouter>,
    });
    act(() => result.current.setFilters({ windowDays: 15 }));
    expect(result.current.filters.windowDays).toBe(15);
    expect(result.current.filters.day).toBeNull();
  });

  it("setting an exact day clears an existing windowDays", () => {
    const { result } = renderHook(() => useFilterState(), {
      wrapper: ({ children }) => <MemoryRouter initialEntries={["/?w=30"]}>{children}</MemoryRouter>,
    });
    act(() => result.current.setFilters({ day: "2026-09-01" }));
    expect(result.current.filters.day).toBe("2026-09-01");
    expect(result.current.filters.windowDays).toBeNull();
  });
});

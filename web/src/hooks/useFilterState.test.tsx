import { describe, expect, it } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { useFilterState } from "./useFilterState";

describe("useFilterState intensity param", () => {
  it("defaults intensity to null when `a4` is absent", () => {
    const { result } = renderHook(() => useFilterState(), {
      wrapper: ({ children }) => <MemoryRouter initialEntries={["/"]}>{children}</MemoryRouter>,
    });
    expect(result.current.filters.intensity).toBeNull();
  });

  it("round-trips a selected intensity through the `a4` URL param", () => {
    const { result } = renderHook(() => useFilterState(), {
      wrapper: ({ children }) => <MemoryRouter initialEntries={["/"]}>{children}</MemoryRouter>,
    });
    act(() => {
      result.current.setFilters({ intensity: "Ειρηνική" });
    });
    expect(result.current.filters.intensity).toBe("Ειρηνική");
  });

  it("reads an initial intensity from the `a4` param", () => {
    const { result } = renderHook(() => useFilterState(), {
      wrapper: ({ children }) => (
        <MemoryRouter initialEntries={[`/?a4=${encodeURIComponent("Ειρηνική")}`]}>{children}</MemoryRouter>
      ),
    });
    expect(result.current.filters.intensity).toBe("Ειρηνική");
  });

  it("clearing intensity removes the `a4` param", () => {
    const { result } = renderHook(() => useFilterState(), {
      wrapper: ({ children }) => (
        <MemoryRouter initialEntries={[`/?a4=${encodeURIComponent("Ειρηνική")}`]}>{children}</MemoryRouter>
      ),
    });
    act(() => result.current.setFilters({ intensity: null }));
    expect(result.current.filters.intensity).toBeNull();
  });

  it("round-trips a value containing a literal comma", () => {
    const { result } = renderHook(() => useFilterState(), {
      wrapper: ({ children }) => <MemoryRouter initialEntries={["/"]}>{children}</MemoryRouter>,
    });
    const value = "Διαταρακτική";
    act(() => result.current.setFilters({ intensity: value }));
    expect(result.current.filters.intensity).toBe(value);
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

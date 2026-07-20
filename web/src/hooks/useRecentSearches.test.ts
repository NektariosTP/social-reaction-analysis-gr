import { describe, expect, it, beforeEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useRecentSearches } from "./useRecentSearches";

describe("useRecentSearches", () => {
  beforeEach(() => sessionStorage.clear());

  it("starts empty", () => {
    const { result } = renderHook(() => useRecentSearches());
    expect(result.current.recent).toEqual([]);
  });

  it("adds a search term to the front of the list", () => {
    const { result } = renderHook(() => useRecentSearches());
    act(() => result.current.addRecent("Athens"));
    expect(result.current.recent).toEqual(["Athens"]);
  });

  it("de-duplicates and moves a repeated term back to the front", () => {
    const { result } = renderHook(() => useRecentSearches());
    act(() => result.current.addRecent("Athens"));
    act(() => result.current.addRecent("Crete"));
    act(() => result.current.addRecent("Athens"));
    expect(result.current.recent).toEqual(["Athens", "Crete"]);
  });

  it("caps the list at 5 entries", () => {
    const { result } = renderHook(() => useRecentSearches());
    for (const term of ["a", "b", "c", "d", "e", "f"]) {
      act(() => result.current.addRecent(term));
    }
    expect(result.current.recent).toHaveLength(5);
    expect(result.current.recent).toEqual(["f", "e", "d", "c", "b"]);
  });

  it("ignores blank input", () => {
    const { result } = renderHook(() => useRecentSearches());
    act(() => result.current.addRecent("   "));
    expect(result.current.recent).toEqual([]);
  });
});

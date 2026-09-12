import { describe, expect, it, beforeEach, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useIsMobile } from "./useIsMobile";

type Listener = (e: { matches: boolean }) => void;

function mockMatchMedia(initialMatches: boolean) {
  let listeners: Listener[] = [];
  const mql = {
    matches: initialMatches,
    media: "(max-width: 640px)",
    addEventListener: (_: string, cb: Listener) => listeners.push(cb),
    removeEventListener: (_: string, cb: Listener) => {
      listeners = listeners.filter((l) => l !== cb);
    },
  };
  window.matchMedia = vi.fn().mockReturnValue(mql) as unknown as typeof window.matchMedia;
  return {
    emit(matches: boolean) {
      mql.matches = matches;
      listeners.forEach((l) => l({ matches }));
    },
  };
}

describe("useIsMobile", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("returns true when the media query matches", () => {
    mockMatchMedia(true);
    const { result } = renderHook(() => useIsMobile());
    expect(result.current).toBe(true);
  });

  it("returns false when the media query does not match", () => {
    mockMatchMedia(false);
    const { result } = renderHook(() => useIsMobile());
    expect(result.current).toBe(false);
  });

  it("updates when the viewport crosses the breakpoint", () => {
    const mm = mockMatchMedia(false);
    const { result } = renderHook(() => useIsMobile());
    expect(result.current).toBe(false);
    act(() => mm.emit(true));
    expect(result.current).toBe(true);
  });
});

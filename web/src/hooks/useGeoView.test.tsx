import { describe, expect, it } from "vitest";
import { act, renderHook } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { useGeoView } from "./useGeoView";

function wrapper(initial: string) {
  return ({ children }: { children: React.ReactNode }) => (
    <MemoryRouter initialEntries={[initial]}>{children}</MemoryRouter>
  );
}

describe("useGeoView", () => {
  it("derives none with no params", () => {
    const { result } = renderHook(() => useGeoView(), { wrapper: wrapper("/") });
    expect(result.current.level).toBe("none");
  });

  it("derives periphery from region", () => {
    const { result } = renderHook(() => useGeoView(), { wrapper: wrapper("/?region=Attica") });
    expect(result.current.level).toBe("periphery");
    expect(result.current.region).toBe("Attica");
  });

  it("ignores muni without region (drill-down invariant)", () => {
    const { result } = renderHook(() => useGeoView(), { wrapper: wrapper("/?muni=X") });
    expect(result.current.level).toBe("none");
  });

  it("derives municipality when both present", () => {
    const { result } = renderHook(() => useGeoView(), {
      wrapper: wrapper("/?region=Attica&muni=Δήμος Αθηναίων"),
    });
    expect(result.current.level).toBe("municipality");
    expect(result.current.municipality).toBe("Δήμος Αθηναίων");
  });

  it("selectPeriphery sets region and clears a prior muni", () => {
    const { result } = renderHook(() => useGeoView(), {
      wrapper: wrapper("/?region=Attica&muni=Δήμος Αθηναίων"),
    });
    act(() => result.current.selectPeriphery("Crete"));
    expect(result.current.region).toBe("Crete");
    expect(result.current.municipality).toBeNull();
    expect(result.current.level).toBe("periphery");
  });

  it("selectMunicipality is a no-op without a region", () => {
    const { result } = renderHook(() => useGeoView(), { wrapper: wrapper("/") });
    act(() => result.current.selectMunicipality("Δήμος Αθηναίων"));
    expect(result.current.level).toBe("none");
  });

  it("clearMunicipality returns to periphery; clear returns to none", () => {
    const { result } = renderHook(() => useGeoView(), {
      wrapper: wrapper("/?region=Attica&muni=Δήμος Αθηναίων"),
    });
    act(() => result.current.clearMunicipality());
    expect(result.current.level).toBe("periphery");
    act(() => result.current.clear());
    expect(result.current.level).toBe("none");
  });
});

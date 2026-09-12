import { useEffect, useState } from "react";

const QUERY = "(max-width: 640px)";

/** Reactive phone-breakpoint flag. Returns false when matchMedia is absent
 * (SSR / test environments that don't mock it). */
export function useIsMobile(): boolean {
  const [isMobile, setIsMobile] = useState(() =>
    typeof window !== "undefined" && typeof window.matchMedia === "function"
      ? window.matchMedia(QUERY).matches
      : false,
  );

  useEffect(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") return;
    const mql = window.matchMedia(QUERY);
    const onChange = (e: MediaQueryListEvent) => setIsMobile(e.matches);
    setIsMobile(mql.matches);
    mql.addEventListener("change", onChange);
    return () => mql.removeEventListener("change", onChange);
  }, []);

  return isMobile;
}

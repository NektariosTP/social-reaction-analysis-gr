import { useCallback, useState } from "react";

const KEY = "reaction-map:recent-searches";
const MAX_ENTRIES = 5;

function load(): string[] {
  try {
    const raw = sessionStorage.getItem(KEY);
    return raw ? (JSON.parse(raw) as string[]) : [];
  } catch {
    return [];
  }
}

/** Session-only (not account-tied) recent search terms, flightradar24-style. */
export function useRecentSearches() {
  const [recent, setRecent] = useState<string[]>(load);

  const addRecent = useCallback((term: string) => {
    const trimmed = term.trim();
    if (!trimmed) return;
    setRecent((prev) => {
      const next = [trimmed, ...prev.filter((t) => t !== trimmed)].slice(0, MAX_ENTRIES);
      sessionStorage.setItem(KEY, JSON.stringify(next));
      return next;
    });
  }, []);

  return { recent, addRecent };
}

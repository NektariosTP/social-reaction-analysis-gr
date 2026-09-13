import { useEffect } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MainView } from "./pages/MainView";
import { useLang } from "./hooks/useLang";

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, refetchOnWindowFocus: false } },
});

/** Keeps <html lang> in step with the active UI language. Crucial for Greek:
 * CSS `text-transform: uppercase` only applies Greek casing rules (which drop
 * the monotonic tonos in all-caps — e.g. "Δικαιώματα" → "ΔΙΚΑΙΩΜΑΤΑ", not
 * "ΔΙΚΑΙΏΜΑΤΑ") when the browser knows the text is Greek. */
function LangSync() {
  const [lang] = useLang();
  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);
  return null;
}

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <LangSync />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<MainView />} />
          <Route path="/cluster/:id" element={<MainView />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

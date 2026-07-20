import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MainView } from "./pages/MainView";
import { StatsPage } from "./pages/StatsPage";
import { NlpEventPage } from "./pages/NlpEventPage";
import { AboutPage } from "./pages/AboutPage";
import { MobileNotice } from "./components/layout";

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, refetchOnWindowFocus: false } },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <MobileNotice />
        <Routes>
          <Route path="/" element={<MainView />} />
          <Route path="/cluster/:id" element={<MainView />} />
          <Route path="/stats" element={<StatsPage />} />
          <Route path="/event/:id" element={<NlpEventPage />} />
          <Route path="/about" element={<AboutPage />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

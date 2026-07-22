import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MainView } from "./MainView";
import styles from "./MainView.module.css";

vi.mock("../components/map", () => ({
  MapView: () => <div data-testid="mock-map" />,
  MapLegend: () => null,
}));

vi.mock("../hooks/useOnboardingSeen", () => ({
  useOnboardingSeen: () => ({ seen: true, dismiss: vi.fn() }),
}));

vi.mock("../api/queries", () => ({
  useEvents: () => ({ data: [], isLoading: false, isError: false }),
  useEventsGeoJSON: () => ({ data: { features: [] }, isLoading: false, isError: false }),
  useRecentEventsCount: () => ({ data: 0 }),
  useEvent: () => ({ data: undefined, isLoading: true, isError: false }),
  applyClientFilters: (entities: unknown[]) => entities,
}));

function renderMainView(initialPath = "/") {
  const queryClient = new QueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialPath]}>
        <Routes>
          <Route path="/" element={<MainView />} />
          <Route path="/cluster/:id" element={<MainView />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("MainView layout", () => {
  it("renders the map, header block, and footer bar with no view-mode tabs", () => {
    renderMainView();
    expect(screen.getByTestId("mock-map")).toBeInTheDocument();
    expect(screen.queryByText("Split + Editorial")).not.toBeInTheDocument();
    expect(screen.queryByText("Immersive")).not.toBeInTheDocument();
    expect(screen.getByText("GitHub")).toBeInTheDocument();
  });

  it("wraps the header block in the styled container that gives it a background", () => {
    const { container } = renderMainView();
    expect(container.querySelector(`.${styles.headerBlock}`)).not.toBeNull();
  });
});

describe("MainView routed detail state", () => {
  it("renders the editorial block in detail mode when mounted at /cluster/:id", () => {
    renderMainView("/cluster/evt-1");
    expect(screen.queryByText(/today's reactions/i)).not.toBeInTheDocument();
  });
});

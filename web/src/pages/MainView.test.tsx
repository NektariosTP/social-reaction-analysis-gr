import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Routes, Route, useLocation } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import userEvent from "@testing-library/user-event";
import { MainView } from "./MainView";
import styles from "./MainView.module.css";

function LocationProbe() {
  const location = useLocation();
  return <div data-testid="location-probe">{location.pathname + location.search}</div>;
}

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
  useOngoingEvents: () => ({ data: [], isLoading: false, isError: false }),
  useUpcomingEvents: () => ({ data: [], isLoading: false, isError: false }),
  useEvent: () => ({ data: undefined, isLoading: true, isError: false }),
  applyClientFilters: (entities: unknown[]) => entities,
  partitionByNational: (events: { is_national?: boolean }[]) => ({
    panhellenic: events.filter((e) => e.is_national),
    other: events.filter((e) => !e.is_national),
  }),
}));

function renderMainView(initialPath = "/") {
  const queryClient = new QueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialPath]}>
        <LocationProbe />
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

describe("MainView preserves filter state when navigating to detail", () => {
  it("keeps active filters in the URL after leaving the cluster detail view", async () => {
    const user = userEvent.setup();
    renderMainView("/cluster/evt-1?a4=%CE%95%CE%B9%CF%81%CE%B7%CE%BD%CE%B9%CE%BA%CE%AE");

    expect(screen.getByTestId("location-probe")).toHaveTextContent("a4=");

    await user.click(screen.getByRole("button", { name: /back/i }));

    expect(screen.getByTestId("location-probe")).toHaveTextContent("a4=");
  });
});

describe("MainView temporal block", () => {
  it("shows the temporal block in list mode", () => {
    renderMainView("/");
    expect(screen.getByRole("button", { name: /upcoming/i })).toBeInTheDocument();
  });

  it("hides the temporal block in detail mode", () => {
    renderMainView("/cluster/evt-1");
    expect(screen.queryByRole("button", { name: /upcoming/i })).not.toBeInTheDocument();
  });
});

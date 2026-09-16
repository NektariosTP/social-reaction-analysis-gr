import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { ClusterDetailContent } from "./ClusterDetailContent";
import { useEvent } from "../../api/queries";

const locatedEvent = {
  id: "evt-1",
  action_forms: ["Κατάληψη"],
  thematic_fields: [],
  channel: null,
  intensity: null,
  summary_el: null,
  summary_en: "Test narrative",
  article_count: 4,
  source_count: 2,
  articles: [],
  lat: 37.9838,
  lon: 23.7275,
};

vi.mock("../../api/queries", () => ({
  useEvent: vi.fn(() => ({
    data: {
      id: "evt-1",
      action_forms: ["Κατάληψη"],
      thematic_fields: [],
      channel: null,
      intensity: null,
      summary_el: null,
      summary_en: "Test narrative",
      article_count: 4,
      source_count: 2,
      articles: [],
    },
    isLoading: false,
    isError: false,
  })),
}));

vi.mock("../map", () => ({ MapView: () => <div className="maplibregl-map" data-testid="mini-map" /> }));

describe("ClusterDetailContent", () => {
  it("renders the summary once (no duplicate narrative section) and a classification section", () => {
    render(
      <MemoryRouter>
        <ClusterDetailContent eventId="evt-1" />
      </MemoryRouter>,
    );
    expect(screen.getAllByText("Test narrative")).toHaveLength(1);
    expect(screen.getByText("Classification")).toBeInTheDocument();
    expect(screen.queryByText(/source breakdown/i)).not.toBeInTheDocument();
  });

  it("does not embed a map in the cluster detail column", () => {
    vi.mocked(useEvent).mockReturnValueOnce({
      data: locatedEvent,
      isLoading: false,
      isError: false,
    } as unknown as ReturnType<typeof useEvent>);
    const { container } = render(
      <MemoryRouter>
        <ClusterDetailContent eventId="evt-1" />
      </MemoryRouter>,
    );
    expect(container.querySelector(".maplibregl-map")).toBeNull();
  });

  it("counts sources from source_count, not the (possibly truncated) article array", () => {
    vi.mocked(useEvent).mockReturnValueOnce({
      data: {
        ...locatedEvent,
        source_count: 47,
        // The API caps the articles array; the header must not count it.
        articles: Array.from({ length: 20 }, (_, i) => ({ id: `a${i}` })),
        reactions: [{ id: "r1", actor_name: "ΠΑΜΕ" }],
      },
      isLoading: false,
      isError: false,
    } as unknown as ReturnType<typeof useEvent>);
    render(
      <MemoryRouter>
        <ClusterDetailContent eventId="evt-1" />
      </MemoryRouter>,
    );
    expect(
      screen.getByText((_, el) => el?.textContent === "Sources (47)"),
    ).toBeInTheDocument();
  });

  it("hides the headline when showHeadline is false", () => {
    render(
      <MemoryRouter>
        <ClusterDetailContent eventId="evt-1" showHeadline={false} />
      </MemoryRouter>,
    );
    expect(screen.queryByText("Test narrative")).not.toBeInTheDocument();
  });

  it("renders the temporal banner when the event has a scheduled time or unions", async () => {
    vi.mocked(useEvent).mockReturnValueOnce({
      data: {
        ...locatedEvent,
        temporal_status: "today",
        event_time: "2026-01-01T09:00:00Z",
        announced_by: "ΓΣΕΕ",
        participating_unions: ["ΓΣΕΕ"],
      },
      isLoading: false,
      isError: false,
    } as unknown as ReturnType<typeof useEvent>);
    render(
      <MemoryRouter>
        <ClusterDetailContent eventId="evt-1" />
      </MemoryRouter>,
    );
    expect(await screen.findByText(/ΓΣΕΕ/)).toBeInTheDocument();
  });
});

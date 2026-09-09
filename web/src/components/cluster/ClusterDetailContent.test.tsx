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
  it("renders the cluster narrative and classification sections", () => {
    render(
      <MemoryRouter>
        <ClusterDetailContent eventId="evt-1" />
      </MemoryRouter>,
    );
    expect(screen.getAllByText("Test narrative").length).toBeGreaterThan(0);
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
});

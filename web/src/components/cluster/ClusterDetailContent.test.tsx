import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { ClusterDetailContent } from "./ClusterDetailContent";

vi.mock("../../api/queries", () => ({
  useEvent: () => ({
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
  }),
}));

vi.mock("../map", () => ({ MapView: () => <div data-testid="mini-map" /> }));

describe("ClusterDetailContent", () => {
  it("renders the cluster narrative and classification sections", () => {
    render(
      <MemoryRouter>
        <ClusterDetailContent eventId="evt-1" />
      </MemoryRouter>,
    );
    expect(screen.getAllByText("Test narrative").length).toBeGreaterThan(0);
  });
});

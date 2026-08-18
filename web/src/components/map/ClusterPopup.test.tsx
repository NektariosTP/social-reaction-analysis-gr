import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
vi.mock("maplibre-gl");
import type maplibregl from "maplibre-gl";
import { ClusterPopup } from "./ClusterPopup";

vi.mock("../../api/queries", () => ({
  useEvent: () => ({
    data: {
      id: "evt-1",
      action_forms: [],
      thematic_fields: [],
      channel: null,
      intensity: null,
      summary_el: null,
      summary_en: "Preview headline",
      source_count: 2,
      articles: [],
    },
    isLoading: false,
    isError: false,
  }),
}));

const fakeMap = {} as unknown as maplibregl.Map;

describe("ClusterPopup", () => {
  it("renders the headline and source count from the fetched event", () => {
    render(<ClusterPopup map={fakeMap} eventId="evt-1" coordinates={[23.7, 38.0]} onClose={vi.fn()} />);
    expect(screen.getByText("Preview headline")).toBeInTheDocument();
    expect(screen.getByText(/2/)).toBeInTheDocument();
  });

  it("shows a Read More button and calls onReadMore with the event id when provided", () => {
    const onReadMore = vi.fn();
    render(
      <ClusterPopup
        map={fakeMap}
        eventId="evt-1"
        coordinates={[23.7, 38.0]}
        onClose={vi.fn()}
        onReadMore={onReadMore}
      />,
    );
    fireEvent.click(screen.getByText("Read More →"));
    expect(onReadMore).toHaveBeenCalledWith("evt-1");
  });

  it("omits the Read More button when onReadMore is not provided", () => {
    render(<ClusterPopup map={fakeMap} eventId="evt-1" coordinates={[23.7, 38.0]} onClose={vi.fn()} />);
    expect(screen.queryByText("Read More →")).not.toBeInTheDocument();
  });

  it("calls onClose when the close button is clicked", () => {
    const onClose = vi.fn();
    render(<ClusterPopup map={fakeMap} eventId="evt-1" coordinates={[23.7, 38.0]} onClose={onClose} />);
    fireEvent.click(screen.getByLabelText("Close"));
    expect(onClose).toHaveBeenCalled();
  });
});

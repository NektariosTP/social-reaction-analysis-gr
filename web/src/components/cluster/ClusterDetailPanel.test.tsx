import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ClusterDetailPanel } from "./ClusterDetailPanel";

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

describe("ClusterDetailPanel", () => {
  it("calls onReadMore with the event id when Read More is clicked", () => {
    const onReadMore = vi.fn();
    render(<ClusterDetailPanel eventId="evt-1" onClose={vi.fn()} onReadMore={onReadMore} />);
    fireEvent.click(screen.getByText("Read More →"));
    expect(onReadMore).toHaveBeenCalledWith("evt-1");
  });

  it("calls onClose when the close button is clicked", () => {
    const onClose = vi.fn();
    render(<ClusterDetailPanel eventId="evt-1" onClose={onClose} onReadMore={vi.fn()} />);
    fireEvent.click(screen.getByLabelText("Close"));
    expect(onClose).toHaveBeenCalled();
  });
});

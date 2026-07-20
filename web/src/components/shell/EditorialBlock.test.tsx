import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { EditorialBlock, type EditorialBlockListProps } from "./EditorialBlock";
import type { EventSummary } from "../../client/types.gen";

vi.mock("../cluster", () => ({
  ClusterDetailContent: ({ eventId }: { eventId: string }) => (
    <div data-testid="detail-content">{eventId}</div>
  ),
}));

const events: EventSummary[] = [
  { id: "evt-1", action_forms: [], thematic_fields: [], channel: null, intensity: null, summary_en: "First event", summary_el: null, article_count: 3, source_count: 1, status: "active", last_seen: "2026-01-01T00:00:00Z" },
  { id: "evt-2", action_forms: [], thematic_fields: [], channel: null, intensity: null, summary_en: "Second event", summary_el: null, article_count: 3, source_count: 1, status: "active", last_seen: "2026-01-01T00:00:00Z" },
];

function renderList(overrides: Partial<EditorialBlockListProps> = {}) {
  const props = {
    mode: "list" as const,
    kpi: { active: 2, locations: 1, newLastHour: 0 },
    events,
    eventsLoading: false,
    eventsError: false,
    highlightedEventId: null,
    onSelectEvent: vi.fn(),
    onBack: vi.fn(),
    ...overrides,
  };
  render(
    <MemoryRouter>
      <EditorialBlock {...props} />
    </MemoryRouter>,
  );
  return props;
}

describe("EditorialBlock", () => {
  it("renders the KPI strip and feed list in list mode", () => {
    renderList();
    expect(screen.getByText("First event")).toBeInTheDocument();
    expect(screen.getByText("Second event")).toBeInTheDocument();
  });

  it("calls onSelectEvent when a story card is opened", () => {
    const props = renderList();
    screen.getByText("First event").click();
    expect(props.onSelectEvent).toHaveBeenCalledWith("evt-1");
  });

  it("marks the highlighted event's card distinctly", () => {
    renderList({ highlightedEventId: "evt-2" });
    const card = screen.getByText("Second event").closest("[data-event-id]");
    expect(card).toHaveAttribute("data-highlighted", "true");
  });

  it("renders ClusterDetailContent and a back control in detail mode", () => {
    const props = {
      mode: "detail" as const,
      kpi: { active: 0, locations: 0, newLastHour: 0 },
      events: [],
      eventsLoading: false,
      eventsError: false,
      highlightedEventId: null,
      onSelectEvent: vi.fn(),
      detailEventId: "evt-1",
      onBack: vi.fn(),
    };
    render(
      <MemoryRouter>
        <EditorialBlock {...props} />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("detail-content")).toHaveTextContent("evt-1");
    screen.getByRole("button", { name: /back/i }).click();
    expect(props.onBack).toHaveBeenCalled();
  });
});

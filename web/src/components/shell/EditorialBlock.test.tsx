import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { EditorialBlock, type EditorialBlockListProps } from "./EditorialBlock";
import type { EventSummary } from "../../client/types.gen";

vi.mock("../cluster", () => ({
  ClusterDetailContent: ({ eventId }: { eventId: string }) => (
    <div data-testid="detail-content">{eventId}</div>
  ),
  InlineAnalysis: ({ eventId }: { eventId: string }) => (
    <div data-inline-detail={eventId}>{eventId}</div>
  ),
}));

const events: EventSummary[] = [
  { id: "evt-1", action_forms: [], thematic_fields: [], channel: null, intensity: null, summary_en: "First event", summary_el: null, article_count: 3, source_count: 1, status: "active", last_seen: "2026-01-01T00:00:00Z" },
  { id: "evt-2", action_forms: [], thematic_fields: [], channel: null, intensity: null, summary_en: "Second event", summary_el: null, article_count: 3, source_count: 1, status: "active", last_seen: "2026-01-01T00:00:00Z" },
];

function renderList(overrides: Partial<EditorialBlockListProps> = {}) {
  const props = {
    mode: "list" as const,
    events,
    eventsLoading: false,
    eventsError: false,
    highlightedEventId: null,
    onSelectEvent: vi.fn(),
    onBack: vi.fn(),
    ...overrides,
  };
  const { container } = render(
    <MemoryRouter>
      <EditorialBlock {...props} />
    </MemoryRouter>,
  );
  return { ...props, container };
}

describe("EditorialBlock", () => {
  it("renders the events and total-articles KPI cells", () => {
    const { container } = renderList();
    const kpiStrip = container.querySelector('[class*="kpiStrip"]');
    expect(kpiStrip).not.toBeNull();
    // events count = 2, Σ article_count = 6
    expect(kpiStrip).toHaveTextContent("2events");
    expect(kpiStrip).toHaveTextContent("6articles");
    expect(screen.getByText("First event")).toBeInTheDocument();
    expect(screen.getByText("Second event")).toBeInTheDocument();
  });

  it("no longer renders the old KPI labels", () => {
    renderList();
    expect(screen.queryByText("active events")).not.toBeInTheDocument();
    expect(screen.queryByText(/last hour/i)).not.toBeInTheDocument();
    expect(screen.queryByText("Today's Events")).not.toBeInTheDocument();
    expect(screen.queryByText(/sources/)).not.toBeInTheDocument();
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

  it("renders inline detail for the expanded event only", () => {
    renderList({ highlightedEventId: "evt-2", expandedId: "evt-2" });
    const detail = document.querySelector('[data-inline-detail="evt-2"]');
    expect(detail).toBeInTheDocument();
    expect(document.querySelector('[data-inline-detail="evt-1"]')).not.toBeInTheDocument();
  });

  it("renders detail content below the back button in detail mode", () => {
    render(
      <MemoryRouter>
        <EditorialBlock mode="detail" detailEventId="evt-1" onBack={vi.fn()} />
      </MemoryRouter>,
    );
    const backBtn = screen.getByText(/back/i);
    const detailContent = screen.getByTestId("detail-content");
    expect(backBtn).toBeInTheDocument();
    expect(detailContent).toBeInTheDocument();
    // back button is a sibling above the content, not wrapping it
    expect(backBtn.contains(detailContent)).toBe(false);
  });

  it("renders feed events in sortEventsForFeed order (upcoming first)", () => {
    const past: EventSummary = {
      id: "past",
      action_forms: [],
      thematic_fields: [],
      channel: null,
      intensity: null,
      summary_en: "Past event",
      summary_el: null,
      article_count: 1,
      source_count: 1,
      status: "active",
      temporal_status: "past",
      last_seen: "2026-01-05T00:00:00Z",
    };
    const upcoming: EventSummary = {
      id: "up",
      action_forms: [],
      thematic_fields: [],
      channel: null,
      intensity: null,
      summary_en: "Upcoming event",
      summary_el: null,
      article_count: 1,
      source_count: 1,
      status: "active",
      temporal_status: "upcoming",
      event_time: "2026-01-10T09:00:00Z",
      last_seen: "2026-01-01T00:00:00Z",
    };
    renderList({ events: [past, upcoming] });
    const cards = Array.from(document.querySelectorAll<HTMLElement>("[data-event-id]"));
    expect(cards.map((c) => c.dataset.eventId)).toEqual(["up", "past"]);
  });
});

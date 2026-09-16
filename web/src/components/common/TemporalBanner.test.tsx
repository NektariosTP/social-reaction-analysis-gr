import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import type { EventSummary } from "../../client/types.gen";
import { TemporalBanner } from "./TemporalBanner";

function ev(over: Partial<EventSummary> = {}): EventSummary {
  return {
    id: "e1",
    action_forms: [],
    thematic_fields: [],
    channel: null,
    intensity: null,
    summary_el: "EL",
    summary_en: "EN",
    article_count: 0,
    source_count: 0,
    status: "enriched",
    last_seen: "2026-01-01T00:00:00Z",
    ...over,
  } as EventSummary;
}

describe("TemporalBanner", () => {
  it("renders a today chip for a today event", () => {
    render(<TemporalBanner event={ev({ temporal_status: "today", event_time: "2026-01-01T09:00:00Z" })} />);
    expect(screen.getByText(/today/i)).toBeInTheDocument();
  });

  it("renders the announcing union and joined-by unions", () => {
    render(
      <TemporalBanner
        event={ev({
          temporal_status: "upcoming",
          event_time: "2026-01-10T09:00:00Z",
          announced_by: "ΓΣΕΕ",
          participating_unions: ["ΓΣΕΕ", "ΑΔΕΔΥ", "ΠΟΕ-ΟΤΑ"],
        })}
      />,
    );
    expect(screen.getByText(/ΓΣΕΕ/)).toBeInTheDocument();
    expect(screen.getByText(/joined by/i)).toBeInTheDocument();
    expect(screen.getByText(/ΑΔΕΔΥ/)).toBeInTheDocument();
  });

  it("renders unions even with no scheduled time", () => {
    const { container } = render(
      <TemporalBanner event={ev({ temporal_status: null, event_time: null, announced_by: "ΟΛΜΕ", participating_unions: ["ΟΛΜΕ"] })} />,
    );
    expect(container.firstChild).not.toBeNull();
    expect(screen.getByText(/ΟΛΜΕ/)).toBeInTheDocument();
  });

  it("renders nothing when there is neither time nor unions", () => {
    const { container } = render(<TemporalBanner event={ev({ temporal_status: null, event_time: null, participating_unions: [] })} />);
    expect(container.firstChild).toBeNull();
  });
});

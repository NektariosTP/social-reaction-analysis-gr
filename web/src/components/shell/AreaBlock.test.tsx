import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { AreaBlock } from "./AreaBlock";
import type { EventSummary } from "../../client/types.gen";

function evt(over: Partial<EventSummary> = {}): EventSummary {
  return {
    id: "e", action_forms: ["Απεργία/Στάση εργασίας"], thematic_fields: ["Εργασιακό"],
    channel: "Φυσικό", intensity: "Ειρηνική", summary_el: "ε", summary_en: "e",
    lat: null, lon: null, region_code: "Attica", municipality: null,
    article_count: 1, source_count: 1, first_seen: null, last_seen: null,
    status: "enriched", event_time: null, temporal_status: null, is_national: false,
    ...over,
  } as EventSummary;
}

describe("AreaBlock", () => {
  it("renders the title and event count", () => {
    render(<AreaBlock title="Attica" events={[evt(), evt()]} loading={false} onClose={vi.fn()} />);
    expect(screen.getByText("Attica")).toBeInTheDocument();
    expect(screen.getByText("2 events")).toBeInTheDocument();
  });

  it("renders an empty state when there are no events", () => {
    render(<AreaBlock title="Crete" events={[]} loading={false} onClose={vi.fn()} />);
    expect(screen.getByText(/no events/i)).toBeInTheDocument();
  });

  it("calls onClose when the close control is clicked", () => {
    const onClose = vi.fn();
    render(<AreaBlock title="Attica" events={[evt()]} loading={false} onClose={onClose} />);
    fireEvent.click(screen.getByRole("button", { name: /close/i }));
    expect(onClose).toHaveBeenCalledOnce();
  });
});

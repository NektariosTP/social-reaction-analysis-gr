import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import type { EventSummary } from "../../client/types.gen";
import { TemporalBlock } from "./TemporalBlock";

function ev(id: string, over: Partial<EventSummary> = {}): EventSummary {
  return {
    id,
    is_national: false,
    action_forms: [],
    thematic_fields: [],
    channel: null,
    intensity: null,
    summary_el: `EL ${id}`,
    summary_en: `EN ${id}`,
    article_count: 0,
    source_count: 0,
    status: "enriched",
    ...over,
  } as EventSummary;
}

function renderBlock(over: Partial<Parameters<typeof TemporalBlock>[0]> = {}) {
  const props = {
    ongoing: [] as EventSummary[],
    upcoming: [] as EventSummary[],
    loading: false,
    error: false,
    onSelectEvent: vi.fn(),
    ...over,
  };
  render(<TemporalBlock {...props} />);
  return props;
}

describe("TemporalBlock", () => {
  it("shows tab counts for ongoing and upcoming", () => {
    renderBlock({ ongoing: [ev("a")], upcoming: [ev("b"), ev("c")] });
    expect(screen.getByText(/\(1\)/)).toBeInTheDocument();
    expect(screen.getByText(/\(2\)/)).toBeInTheDocument();
  });

  it("preselects Ongoing when today-events exist", () => {
    renderBlock({ ongoing: [ev("a")], upcoming: [ev("b")] });
    expect(screen.getByText("EN a")).toBeInTheDocument();
    expect(screen.queryByText("EN b")).not.toBeInTheDocument();
  });

  it("preselects Upcoming when there are no ongoing events", () => {
    renderBlock({ ongoing: [], upcoming: [ev("b")] });
    expect(screen.getByText("EN b")).toBeInTheDocument();
  });

  it("splits ongoing into panhellenic and other subsections", () => {
    renderBlock({ ongoing: [ev("nat", { is_national: true }), ev("loc")] });
    expect(screen.getByText("EN nat")).toBeInTheDocument();
    expect(screen.getByText("EN loc")).toBeInTheDocument();
  });

  it("switches tab on click and stays switched", () => {
    renderBlock({ ongoing: [ev("a")], upcoming: [ev("b")] });
    fireEvent.click(screen.getByRole("button", { name: /upcoming/i }));
    expect(screen.getByText("EN b")).toBeInTheDocument();
    expect(screen.queryByText("EN a")).not.toBeInTheDocument();
  });

  it("calls onSelectEvent with the event id when a row is clicked", () => {
    const { onSelectEvent } = renderBlock({ ongoing: [ev("a")] });
    fireEvent.click(screen.getByText("EN a"));
    expect(onSelectEvent).toHaveBeenCalledWith("a");
  });

  it("renders an empty state when a tab has no events", () => {
    renderBlock({ ongoing: [], upcoming: [] });
    expect(screen.getByText(/no upcoming events/i)).toBeInTheDocument();
  });
});

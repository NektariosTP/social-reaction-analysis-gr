import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { StoryCard } from "./StoryCard";
import type { EventSummary } from "../../client/types.gen";

const event: EventSummary = {
  id: "evt-1",
  action_forms: [],
  thematic_fields: [],
  channel: null,
  intensity: null,
  summary_el: "Δοκιμή",
  summary_en: "Test event",
  article_count: 3,
  source_count: 2,
  status: "active",
  last_seen: "2026-01-01T00:00:00Z",
};

describe("StoryCard onOpen", () => {
  it("calls onOpen instead of navigating on a plain click when onOpen is provided", () => {
    const onOpen = vi.fn();
    render(
      <MemoryRouter>
        <StoryCard event={event} onOpen={onOpen} />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByText("Test event"));
    expect(onOpen).toHaveBeenCalledWith("evt-1");
  });

  it("still renders a real href to /cluster/:id for accessibility and modifier-click support", () => {
    render(
      <MemoryRouter>
        <StoryCard event={event} onOpen={vi.fn()} />
      </MemoryRouter>,
    );
    expect(screen.getByText("Test event").closest("a")).toHaveAttribute("href", "/cluster/evt-1");
  });
});

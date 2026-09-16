import { describe, expect, it } from "vitest";
import type { EventSummary } from "../client/types.gen";
import { sortEventsForFeed } from "./sortEvents";

function ev(id: string, over: Partial<EventSummary> = {}): EventSummary {
  return {
    id,
    action_forms: [],
    thematic_fields: [],
    channel: null,
    intensity: null,
    summary_el: `EL ${id}`,
    summary_en: `EN ${id}`,
    article_count: 0,
    source_count: 0,
    status: "enriched",
    last_seen: "2026-01-01T00:00:00Z",
    ...over,
  } as EventSummary;
}

describe("sortEventsForFeed", () => {
  it("puts today+upcoming before past/undated", () => {
    const past = ev("past", { temporal_status: "past", last_seen: "2026-01-05T00:00:00Z" });
    const upcoming = ev("up", { temporal_status: "upcoming", event_time: "2026-01-10T09:00:00Z" });
    const ids = sortEventsForFeed([past, upcoming]).map((e) => e.id);
    expect(ids).toEqual(["up", "past"]);
  });

  it("orders group A by event_time ascending (soonest first)", () => {
    const later = ev("later", { temporal_status: "upcoming", event_time: "2026-01-20T09:00:00Z" });
    const today = ev("today", { temporal_status: "today", event_time: "2026-01-01T09:00:00Z" });
    const soon = ev("soon", { temporal_status: "upcoming", event_time: "2026-01-05T09:00:00Z" });
    const ids = sortEventsForFeed([later, today, soon]).map((e) => e.id);
    expect(ids).toEqual(["today", "soon", "later"]);
  });

  it("breaks same-day group A ties by article_count descending", () => {
    const few = ev("few", { temporal_status: "today", event_time: "2026-01-01T08:00:00Z", article_count: 2 });
    const many = ev("many", { temporal_status: "today", event_time: "2026-01-01T20:00:00Z", article_count: 9 });
    const ids = sortEventsForFeed([few, many]).map((e) => e.id);
    expect(ids).toEqual(["many", "few"]);
  });

  it("orders group B by last_seen descending, tiebreak article_count", () => {
    const old = ev("old", { temporal_status: "past", last_seen: "2026-01-01T00:00:00Z" });
    const recent = ev("recent", { temporal_status: null, last_seen: "2026-01-09T00:00:00Z" });
    const sameDayFew = ev("sf", { temporal_status: null, last_seen: "2026-01-09T02:00:00Z", article_count: 1 });
    const ids = sortEventsForFeed([old, sameDayFew, recent]).map((e) => e.id);
    // recent & sf are same day (Jan 9); recent has 0 articles, sf has 1 -> sf first
    expect(ids).toEqual(["sf", "recent", "old"]);
  });

  it("does not mutate the input array", () => {
    const input = [ev("a", { temporal_status: "past" }), ev("b", { temporal_status: "today", event_time: "2026-01-01T00:00:00Z" })];
    const copy = [...input];
    sortEventsForFeed(input);
    expect(input).toEqual(copy);
  });

  it("returns [] for empty input", () => {
    expect(sortEventsForFeed([])).toEqual([]);
  });
});

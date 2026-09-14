import { describe, expect, it } from "vitest";
import { sourceCountDisplay } from "./sourceDisplay";

describe("sourceCountDisplay", () => {
  it("shows article_count with the articles label when there are articles", () => {
    expect(sourceCountDisplay({ article_count: 4, source_count: 2 })).toEqual({
      count: 4,
      labelKey: "card.articles",
    });
  });

  it("falls back to source_count with the sources label for announcement-only events", () => {
    // The union announcement link itself is a source_count=1+ entry even with zero
    // news article coverage — it must never read as "0 sources".
    expect(sourceCountDisplay({ article_count: 0, source_count: 17 })).toEqual({
      count: 17,
      labelKey: "card.sources",
    });
  });
});

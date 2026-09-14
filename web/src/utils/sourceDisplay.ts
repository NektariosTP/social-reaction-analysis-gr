interface CountedEvent {
  article_count: number;
  source_count: number;
}

/** Announcement-only events have article_count = 0 until news coverage lands,
 * even when backed by many union reaction sources — fall back to source_count
 * rather than showing a misleading "0 articles". */
export function sourceCountDisplay(event: CountedEvent): {
  count: number;
  labelKey: "card.articles" | "card.sources";
} {
  return event.article_count > 0
    ? { count: event.article_count, labelKey: "card.articles" }
    : { count: event.source_count, labelKey: "card.sources" };
}

interface CountedEvent {
  article_count: number;
  source_count: number;
}

/** Announcement-only events have article_count = 0 until news coverage lands,
 * even when backed by many union reaction sources — fall back to source_count
 * rather than showing a misleading "0 articles". The label is pluralized on the
 * count (1 → singular) so it never reads "1 άρθρα". */
export function sourceCountDisplay(event: CountedEvent): {
  count: number;
  labelKey: "card.article" | "card.articles" | "card.source" | "card.sources";
} {
  const usesArticles = event.article_count > 0;
  const count = usesArticles ? event.article_count : event.source_count;
  if (usesArticles) {
    return { count, labelKey: count === 1 ? "card.article" : "card.articles" };
  }
  return { count, labelKey: count === 1 ? "card.source" : "card.sources" };
}

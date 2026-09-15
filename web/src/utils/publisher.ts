/**
 * Human-readable publisher name derived from an article URL.
 *
 * News articles are all stored with source_id "google_news_rss", which is a
 * pipeline label, not a source the reader recognises. The registrable host of
 * the article URL (e.g. "kathimerini.gr") IS the newspaper/blog name, and it's
 * available for every already-ingested row — so we derive it at display time
 * rather than storing a separate publisher column.
 */
export function publisherFromUrl(url: string | null | undefined): string | null {
  if (!url) return null;
  try {
    const host = new URL(url).hostname.toLowerCase();
    return host.replace(/^www\./, "") || null;
  } catch {
    return null;
  }
}

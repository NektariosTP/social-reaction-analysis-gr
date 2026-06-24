SELECT 
    LEFT(e.id::text, 8) as cluster_id, -- Μικρότερο ID για ευκολία
    e.article_count,
    a.title,
    a.canonical_url,
    a.source_id,
    a.ingested_at,
    a.published_at
FROM events e
JOIN articles a ON a.event_id = e.id
ORDER BY e.article_count DESC, e.id, a.ingested_at;
SELECT
    LEFT(e.id::text, 8)                          AS cluster_id,
    e.article_count,
    e.status,
    e.action_forms,
    e.thematic_fields,
    e.channel,
    e.intensity,
    e.classification_confidence,
    a.title,
    e.summary_el,
    e.summary_en,
    ST_Y(e.primary_location::geometry)           AS lat,
    ST_X(e.primary_location::geometry)           AS lon,
    e.first_seen,
    e.last_seen,
    a.canonical_url,
    a.source_id,
    a.published_at
FROM events e
JOIN articles a ON a.event_id = e.id AND a.is_duplicate = FALSE
ORDER BY e.article_count DESC, e.id, a.published_at;

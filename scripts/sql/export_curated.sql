-- Export human-curated events as a ground-truth JSONL for scripts/eval_classify_prod.py.
-- Each enriched event's stored axis labels are curator-verified truth (approved or corrected).
-- Run read-only, tuples-only + unaligned so each row is one raw JSON line (JSONL):
--
--   docker exec -i <db> psql -U <user> -d <db> -tA -f - < export_curated.sql > curated.jsonl
--
-- Adjust the LIMIT to control LLM cost when scoring (each event is re-classified N times).
-- Only status='enriched' events are exported: they are news-detected and therefore have
-- articles to re-classify (announced events are seeded from union feeds, not news bodies).

SELECT json_build_object(
         'event_id',        e.id,
         -- DESC to mirror production, which classifies the 10 newest articles
         -- (enrich/pipeline.py: ORDER BY published_at DESC LIMIT 10)
         'article_titles',  array_agg(a.title      ORDER BY a.published_at DESC),
         'article_bodies',  array_agg(a.body_text  ORDER BY a.published_at DESC),
         'action_forms',    e.action_forms,
         'thematic_fields', e.thematic_fields,
         'channel',         e.channel,
         'intensity',       e.intensity,
         -- curator-verified location as geocoding ground truth (NULL = abstained/venueless)
         'true_lat',        ST_Y(e.primary_location::geometry),
         'true_lon',        ST_X(e.primary_location::geometry),
         'is_national',     e.is_national,
         'is_event',        true,
         'published_at',    MIN(a.published_at)
       )
FROM events e
JOIN articles a ON a.event_id = e.id AND NOT a.is_duplicate
WHERE e.status IN ('enriched','archived')   -- both are curator-verified ground truth
  AND e.channel IS NOT NULL                 -- fully enriched only
GROUP BY e.id
HAVING COUNT(a.id) >= 1
ORDER BY e.id;

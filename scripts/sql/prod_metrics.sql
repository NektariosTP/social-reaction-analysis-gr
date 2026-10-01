-- Production / operational metrics for Evaluation §6.2(a).
-- Read-only. Run on prod:  docker exec -i <db> psql -U <user> -d <db> -f - < prod_metrics.sql
-- NOTE: pipeline_runs.metrics are per-cycle and INCREMENTAL, so their sums measure
-- WORK PERFORMED (an event reprocessed across cycles is counted many times). The count
-- of DISTINCT events comes from the events table, not from these sums. The events table
-- reflects HUMAN-CURATED state (the curator approved/corrected/merged/rejected events).

\echo '== 1. Throughput / work performed (pipeline_runs, NLP phase) =='
SELECT COUNT(*)                                        AS cycles,
       MIN(started_at)::date                           AS first_run,
       MAX(started_at)::date                           AS last_run,
       SUM((metrics->>'n_embedded')::int)              AS articles_embedded,
       SUM((metrics->>'n_clusters')::int)              AS clusters_formed,
       SUM((metrics->>'n_gated_out')::int)             AS noise_gated_out,
       SUM((metrics->>'n_dupes')::int)                 AS duplicates_flagged,
       SUM((metrics->>'n_merges')::int)                AS auto_merges,
       ROUND(AVG((metrics->>'n_embedded')::numeric),1) AS avg_embedded_per_cycle
FROM pipeline_runs;

\echo '== 2. Distinct events by lifecycle status (human-curated) =='
-- accepted (approved/enriched/announced) vs rejected = human triage decision;
-- rejected/(accepted+rejected) approximates the detection false-positive rate;
-- merged approximates clustering over-fragmentation the curator had to fix.
SELECT status, COUNT(*) FROM events GROUP BY status ORDER BY 2 DESC;

\echo '== 3. Enrichment outcomes for live events (enriched + announced) =='
SELECT COUNT(*)                                              AS live_events,
       COUNT(*) FILTER (WHERE primary_location IS NOT NULL)  AS located,
       COUNT(*) FILTER (WHERE primary_location IS NULL)      AS abstained,
       COUNT(*) FILTER (WHERE is_national)                   AS national,
       ROUND(AVG(article_count),1)                           AS avg_articles,
       ROUND(AVG(source_count),1)                            AS avg_sources
FROM events WHERE status IN ('enriched','announced');

\echo '== 4a. Action Form distribution =='
SELECT af AS action_form, COUNT(*) FROM events, unnest(action_forms) af
  WHERE status IN ('enriched','announced') GROUP BY 1 ORDER BY 2 DESC;
\echo '== 4b. Thematic Field distribution =='
SELECT tf AS thematic_field, COUNT(*) FROM events, unnest(thematic_fields) tf
  WHERE status IN ('enriched','announced') GROUP BY 1 ORDER BY 2 DESC;
\echo '== 4c. Channel distribution =='
SELECT channel, COUNT(*) FROM events
  WHERE status IN ('enriched','announced') GROUP BY 1 ORDER BY 2 DESC;
\echo '== 4d. Intensity distribution =='
SELECT intensity, COUNT(*) FROM events
  WHERE status IN ('enriched','announced') GROUP BY 1 ORDER BY 2 DESC;

\echo '== 5. Multi-location events =='
SELECT COUNT(*) AS multi_location_events FROM (
  SELECT event_id FROM event_locations GROUP BY event_id HAVING COUNT(*) > 1
) t;

import { useTranslation } from "react-i18next";
import { AppShell } from "../components/layout";
import { AxisValueChip } from "../components/common/AxisValueChip";
import { AxisReferenceBlock } from "../components/common";
import { ACTION_FORM, THEMATIC_FIELD, CHANNEL, INTENSITY } from "../i18n/taxonomy";
import styles from "./AboutPage.module.css";

const PIPELINE_STEPS = [
  { title: "1 · Ingest", body: "Google News RSS + trafilatura article extraction. Idempotent via content-hash dedup." },
  { title: "2 · Embed", body: "sentence-transformers multilingual embeddings, stored in pgvector." },
  { title: "3 · Cluster", body: "HDBSCAN over embeddings with quality gates (min articles, min intra-cluster similarity)." },
  { title: "4 · Deduplicate", body: "Cosine + time-window matching against the stable event registry." },
  { title: "5 · Enrich", body: "Four-axis classification (zero-shot + LLM fallback), gazetteer/NER/LLM geocoding, bilingual summarisation." },
  { title: "6 · Serve", body: "Read-only FastAPI (/events, /stats) → this map and dashboard." },
];

export function AboutPage() {
  const { t } = useTranslation();

  return (
    <AppShell>
      <div className={styles.header}>
        <h1 className={styles.title}>{t("nav.about")} &amp; Methodology</h1>
        <p className={styles.lead}>
          Reaction Map is a thesis research project (MSc, 2026) combining automated Greek news
          ingestion with NLP clustering and four-axis classification to produce a real-time map
          of collective action in Greece.
        </p>
      </div>

      <div className={styles.grid3}>
        <div className={styles.col}>
          <div className={styles.colLabel}>About the project</div>
          <p className={styles.p}>
            Reaction Map addresses a gap in Greek civil-society data: no unified, machine-readable
            record of collective action events exists. The platform ingests Greek-language news,
            clusters related coverage via NLP, and renders the result as an interactive map and
            dashboard.
          </p>
          <p className={styles.p}>
            The four-axis classification system (A1–A4) — Action Form, Thematic Field, Channel,
            Intensity — is the original scholarly contribution of this thesis, enabling
            multi-label, multi-dimensional indexing that single-label systems miss.
          </p>
          <div className={styles.citation}>
            <div style={{ opacity: 0.55, fontSize: 8, marginBottom: 4 }}>ACADEMIC CITATION</div>
            <div>
              [Author Name]. <i>Reaction Map: A Real-Time NLP System for Classifying Collective
              Action in Greece.</i> MSc Thesis, [University], 2026.
            </div>
          </div>
        </div>

        <div className={styles.col}>
          <div className={styles.colLabel}>Data sources</div>
          <div className={styles.sourceCard}>
            <div className={styles.sourceTitle}>Greek news (live)</div>
            <div className={styles.sourceDesc}>
              Google News RSS + trafilatura article extraction. A spaCy lemma-based relevance
              filter gates articles before embedding.
            </div>
          </div>
          <div className={`${styles.sourceCard} ${styles.sourceCardPlanned}`}>
            <div className={styles.sourceTitle}>Official/union feeds (planned)</div>
            <div className={styles.sourceDesc}>apergia.gr and structured ministry/union feeds.</div>
          </div>
          <div className={`${styles.sourceCard} ${styles.sourceCardPlanned}`}>
            <div className={styles.sourceTitle}>Reddit (planned)</div>
            <div className={styles.sourceDesc}>PRAW OAuth connector for Greek subreddits.</div>
          </div>
          <div className={`${styles.sourceCard} ${styles.sourceCardPlanned}`}>
            <div className={styles.sourceTitle}>Curated X/journalist handles (planned)</div>
            <div className={styles.sourceDesc}>RSS-bridge, ToS-limited.</div>
          </div>
        </div>

        <div className={styles.col}>
          <div className={styles.colLabel}>The 4-axis classification system</div>
          <AxisReferenceBlock label={`${t("filters.axis1")} · multi-label`} color="var(--color-axis1)">
            <div className={styles.chipRow}>
              {Object.keys(ACTION_FORM).map((v) => (
                <AxisValueChip key={v} axis="action" value={v} />
              ))}
            </div>
          </AxisReferenceBlock>
          <AxisReferenceBlock label={`${t("filters.axis2")} · multi-label`} color="var(--color-axis2)">
            <div className={styles.chipRow}>
              {Object.keys(THEMATIC_FIELD).map((v) => (
                <AxisValueChip key={v} axis="theme" value={v} />
              ))}
            </div>
          </AxisReferenceBlock>
          <AxisReferenceBlock label={`${t("filters.axis3")} · single-select`} color="var(--color-axis3)">
            <div className={styles.chipRow}>
              {Object.keys(CHANNEL).map((v) => (
                <AxisValueChip key={v} axis="channel" value={v} />
              ))}
            </div>
          </AxisReferenceBlock>
          <AxisReferenceBlock label={`${t("filters.axis4")} · ordinal`}>
            <div className={styles.chipRow}>
              {Object.keys(INTENSITY).map((v) => (
                <AxisValueChip key={v} axis="intensity" value={v} />
              ))}
            </div>
            <div className={styles.axisNote}>
              Confidence is scored per-axis, not per-label — see a cluster's classification table.
            </div>
          </AxisReferenceBlock>
        </div>
      </div>

      <div className={styles.pipeline}>
        <div className={styles.colLabel}>NLP pipeline overview</div>
        <div className={styles.pipelineRow}>
          {PIPELINE_STEPS.map((step, i) => (
            <div key={step.title} className={`${styles.pipelineStep} ${i === 4 ? styles.pipelineStepActive : ""}`}>
              <div className={styles.pipelineStepTitle}>{step.title}</div>
              <div className={styles.pipelineStepBody}>{step.body}</div>
            </div>
          )).flatMap((el, i) =>
            i < PIPELINE_STEPS.length - 1
              ? [el, <span key={`arrow-${i}`} className={styles.pipelineArrow}>→</span>]
              : [el],
          )}
        </div>
      </div>

      <div className={styles.grid2}>
        <div>
          <div className={styles.colLabel}>Limitations &amp; caveats</div>
          <ul className={styles.limitList}>
            <li>Currently single-sourced from Google News RSS — official feeds, Reddit, and
              curated social handles are architected but not yet live, so coverage skews toward
              outlets Google News indexes.</li>
            <li>A4 intensity classification depends on language signals in the source text;
              understated reporting can under-classify escalation.</li>
            <li>Geocoding resolves to one primary point per event (periphery/point), not the
              multi-location breakdown a single story may actually span.</li>
            <li>Instagram is a documented, deliberate non-source — no compliant ingestion API
              exists.</li>
            <li>Zero-shot classification falls back to an LLM only below a confidence threshold;
              LLM-fallback quality depends on the configured provider.</li>
          </ul>
        </div>
        <div>
          <div className={styles.colLabel}>Contact &amp; code</div>
          <a className={styles.linkRow} href="https://github.com/" target="_blank" rel="noreferrer">
            <span>GitHub repository</span>
            <span style={{ opacity: 0.5 }}>↗</span>
          </a>
          <a className={styles.linkRow} href="mailto:">
            <span>Contact / feedback</span>
            <span style={{ opacity: 0.5 }}>↗</span>
          </a>
          <div className={styles.linkRow}>
            <span>Full thesis PDF</span>
            <span style={{ opacity: 0.5 }}>[university repository]</span>
          </div>
          <p style={{ fontSize: 10, color: "var(--color-text-muted)", marginTop: 12 }}>
            Data for academic, non-commercial use only.
            <br />© 2026 [Author Name] — CC BY-NC 4.0
          </p>
        </div>
      </div>
    </AppShell>
  );
}

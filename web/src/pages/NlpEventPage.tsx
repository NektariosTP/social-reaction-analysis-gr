import { Link, useParams } from "react-router-dom";
import { AppShell } from "../components/layout";
import { ComingSoonBlock } from "../components/common";

/** Per-article NER breakdown (wireframe §04) — deprioritized. The current
 * schema has no per-article NER/entity-extraction record, only per-cluster
 * (Event) classification, so this stays a stub until that data exists. */
export function NlpEventPage() {
  const { id } = useParams<{ id: string }>();
  return (
    <AppShell>
      <div style={{ padding: "var(--space-6) var(--space-5)", maxWidth: 640, margin: "0 auto" }}>
        <ComingSoonBlock
          title="Per-article NLP analysis"
          description={`Will show NER-annotated source text and per-article entity extraction for article ${id ?? ""}, once the pipeline records per-article (not just per-cluster) classification detail.`}
        />
        <p style={{ marginTop: "var(--space-4)" }}>
          <Link to="/">‹ Back to map</Link>
        </p>
      </div>
    </AppShell>
  );
}

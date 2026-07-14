import { ComingSoonBlock } from "../common";
import type { PetitionData } from "./types";

export function PetitionProgress({ data }: { data?: PetitionData }) {
  if (!data) {
    return (
      <ComingSoonBlock
        title="Petition progress"
        description="Will show signature counts against target once a petition-platform connector (Change.org / e-petitions) is added."
      />
    );
  }

  const pct = Math.min(100, Math.round((data.signatures / data.target) * 100));
  return (
    <div>
      <div
        style={{
          height: 9,
          border: "1px solid var(--color-border)",
          borderRadius: "var(--radius-sm)",
          marginBottom: 4,
          overflow: "hidden",
        }}
      >
        <div style={{ height: "100%", width: `${pct}%`, background: "var(--color-accent)" }} />
      </div>
      <div style={{ fontSize: 10, fontWeight: 600, color: "var(--color-text-muted)" }}>
        {data.signatures.toLocaleString()} / {data.target.toLocaleString()} ({pct}%)
      </div>
    </div>
  );
}

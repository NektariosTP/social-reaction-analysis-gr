import { ComingSoonBlock } from "../common";
import type { TrendingHashtag } from "./types";

export function TrendingHashtags({ data }: { data?: TrendingHashtag[] }) {
  if (!data || data.length === 0) {
    return (
      <ComingSoonBlock
        title="Trending hashtags"
        description="Will show hashtags/petitions linked to this cluster with mention counts, once a social-listening source is wired in."
      />
    );
  }

  return (
    <div style={{ display: "flex", gap: 8, alignItems: "center", fontSize: 11, fontWeight: 600 }}>
      <span>🔥</span>
      {data.map((h) => (
        <span
          key={h.tag}
          style={{ border: "1px solid var(--color-border)", borderRadius: "var(--radius-sm)", padding: "2px 7px" }}
        >
          #{h.tag} · {h.mentions.toLocaleString()}
        </span>
      ))}
    </div>
  );
}

import type { ReactionSummary } from "../client/types.gen";

/** Collapses a raw event_reactions list to one entry per union (first occurrence
 * wins, so the announcer's row — always index 0 — is kept over a later duplicate
 * from the same union). Shared by the union list and its section header count so
 * they can never disagree. */
export function dedupeUnions(reactions: ReactionSummary[]): ReactionSummary[] {
  const seen = new Set<string>();
  const out: ReactionSummary[] = [];
  for (const r of reactions) {
    if (seen.has(r.actor_name)) continue;
    seen.add(r.actor_name);
    out.push(r);
  }
  return out;
}

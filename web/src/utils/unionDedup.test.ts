import { describe, expect, it } from "vitest";
import { dedupeUnions } from "./unionDedup";

const r = (id: string, actor_name: string) => ({
  id, actor_name, source_org: actor_name.toLowerCase(),
  url: `http://x/${id}`, observed_at: null, text: null,
});

describe("dedupeUnions", () => {
  it("keeps one entry per union, first occurrence wins", () => {
    const out = dedupeUnions([r("1", "ΠΑΜΕ"), r("2", "ΑΔΕΔΥ"), r("3", "ΑΔΕΔΥ"), r("4", "ΑΔΕΔΥ")]);
    expect(out.map((x) => x.actor_name)).toEqual(["ΠΑΜΕ", "ΑΔΕΔΥ"]);
    expect(out[1].id).toBe("2");
  });

  it("returns an empty list for an empty input", () => {
    expect(dedupeUnions([])).toEqual([]);
  });
});

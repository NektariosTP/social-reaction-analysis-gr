import { describe, expect, it } from "vitest";
import { applyClientFilters } from "./queries";
import { toggleWithAllSentinel } from "../hooks/useFilterState";

const ALL = ["Ειρηνική", "Διαταρακτική (μη βίαιη, παρεμποδιστική)", "Βίαιη/Συγκρουσιακή"];

function entity(intensity: string | null) {
  return { action_forms: [], thematic_fields: [], intensity };
}

describe("applyClientFilters — intensity", () => {
  it("returns everything, including null-intensity entities, when no filter is applied ([])", () => {
    const entities = [entity(ALL[0]), entity(ALL[1]), entity(null)];
    expect(applyClientFilters(entities, { intensities: [] })).toHaveLength(3);
  });

  it("returns nothing once the user explicitly deselects every intensity", () => {
    const noneSelected = toggleWithAllSentinel(ALL, [ALL[0]], ALL[0]);
    const entities = [entity(ALL[0]), entity(ALL[1]), entity(ALL[2]), entity(null)];
    expect(applyClientFilters(entities, { intensities: noneSelected })).toHaveLength(0);
  });
});

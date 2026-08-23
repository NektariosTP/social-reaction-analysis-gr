import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { EventContextPanel } from "./EventContextPanel";

const euro = { key: "unemployment_rate", label_el: "Ανεργία", label_en: "Unemployment", unit: "%", value: 10.5, period: "2023", source: "eurostat", source_url: "http://x" };
const natl = { key: "rule_of_law", label_el: "Κράτος δικαίου", label_en: "Rule of Law", unit: "pctile", value: 70, period: "2023", source: "worldbank", source_url: "http://x" };

vi.mock("../../api/queries", () => ({
  useEventContext: () => ({
    isLoading: false,
    data: { region_code: "Attica", always_on: [euro, natl], thematic: [] },
  }),
}));

describe("EventContextPanel", () => {
  it("labels national rows as national, not periphery-specific", () => {
    render(<EventContextPanel eventId="e1" />);
    expect(screen.getByText(/National — Greece/i)).toBeInTheDocument();
    // the periphery heading carries the region name
    expect(screen.getByText(/Attica/)).toBeInTheDocument();
  });
});

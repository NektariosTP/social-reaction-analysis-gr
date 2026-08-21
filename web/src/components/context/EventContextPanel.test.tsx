import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { EventContextPanel } from "./EventContextPanel";

vi.mock("../../api/queries", () => ({
  useEventContext: () => ({
    isLoading: false, isError: false,
    data: {
      region_code: "Attica",
      always_on: [{ key: "gdp_per_capita", label_el: "ΑΕΠ", label_en: "GDP", unit: "EUR", value: 20000, period: "2022", source: "eurostat", source_url: "http://x" }],
      thematic: [{ key: "at_risk_of_poverty", label_el: "Φτώχεια", label_en: "Poverty", unit: "%", value: 25, period: "2022", source: "eurostat", source_url: "http://x" }],
    },
  }),
}));

describe("EventContextPanel", () => {
  it("renders always-on and thematic indicators", () => {
    render(<EventContextPanel eventId="abc" />);
    expect(screen.getByText(/GDP|ΑΕΠ/)).toBeInTheDocument();
    expect(screen.getByText(/Poverty|Φτώχεια/)).toBeInTheDocument();
  });
});

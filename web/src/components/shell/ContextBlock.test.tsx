import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ContextBlock } from "./ContextBlock";

vi.mock("../../api/queries", () => ({
  useRegionIndicators: (code: string | null) => ({
    isLoading: false, isError: false,
    data: {
      region_code: code ?? "GR",
      always_on: [{ key: "unemployment_rate", label_el: "Ανεργία", label_en: "Unemployment", unit: "%", value: 10.5, period: "2023", source: "eurostat", source_url: "http://x" }],
      thematic: [],
    },
  }),
}));

describe("ContextBlock", () => {
  it("renders national title when no region selected", () => {
    render(<ContextBlock regionCode={null} />);
    expect(screen.getByText(/Unemployment|Ανεργία/)).toBeInTheDocument();
    expect(screen.getByText(/10.5/)).toBeInTheDocument();
  });
});

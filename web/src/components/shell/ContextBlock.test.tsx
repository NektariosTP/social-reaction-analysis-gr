import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { ContextBlock } from "./ContextBlock";

const euro = { key: "unemployment_rate", label_el: "Ανεργία", label_en: "Unemployment", unit: "%", value: 10.5, period: "2023", source: "eurostat", source_url: "http://x" };
const natl = { key: "gdp_growth", label_el: "Ανάπτυξη", label_en: "GDP growth", unit: "%", value: 2.1, period: "2023", source: "worldbank", source_url: "http://x" };

vi.mock("../../api/queries", () => ({
  useRegionIndicators: (code: string | null) => ({
    isLoading: false, isError: false,
    data: {
      region_code: code ?? "GR",
      always_on: code === "GR" ? [natl] : [euro, natl],
      thematic: [],
    },
  }),
  useIndicatorCatalog: () => ({ data: { indicators: [{ key: "unemployment_rate", label_el: "Ανεργία", label_en: "Unemployment", unit: "%" }] } }),
}));

describe("ContextBlock", () => {
  it("national view: single national list, no close button", () => {
    render(<ContextBlock regionCode={null} />);
    expect(screen.getByText(/GDP growth|Ανάπτυξη/)).toBeInTheDocument();
    expect(screen.queryByLabelText(/close/i)).not.toBeInTheDocument();
  });

  it("periphery view: splits rows by source and shows a close button", () => {
    const onClose = vi.fn();
    render(<ContextBlock regionCode="Attica" title="Attica" onClose={onClose} />);
    expect(screen.getByText(/Periphery-specific/i)).toBeInTheDocument();
    expect(screen.getByText(/National — Greece/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/close/i)).toBeInTheDocument();
  });

  it("overlay picker lists catalog indicators when onSelectIndicator is given", () => {
    render(<ContextBlock regionCode={null} onSelectIndicator={() => {}} />);
    expect(screen.getByRole("combobox")).toBeInTheDocument();
  });
});

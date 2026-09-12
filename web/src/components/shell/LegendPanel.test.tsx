import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { LegendPanel } from "./LegendPanel";

describe("LegendPanel", () => {
  it("renders the legend content with no toggle button", () => {
    render(<LegendPanel />);
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
    expect(screen.getByText("Legend")).toBeInTheDocument();
  });
});

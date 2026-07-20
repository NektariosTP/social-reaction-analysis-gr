import { describe, expect, it } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MapLegend } from "./MapLegend";

describe("MapLegend", () => {
  it("is expanded by default, showing intensity, channel, and action-form rows", () => {
    render(<MapLegend />);
    expect(screen.getByText("Peaceful")).toBeInTheDocument();
    expect(screen.getByText("Digital (online)")).toBeInTheDocument();
    expect(screen.getByText("Occupation")).toBeInTheDocument();
  });

  it("collapses when the toggle is clicked, hiding the axis rows", () => {
    render(<MapLegend />);
    fireEvent.click(screen.getByRole("button", { name: /legend/i }));
    expect(screen.queryByText("Peaceful")).not.toBeInTheDocument();
  });

  it("does not mention aggregated cluster markers", () => {
    render(<MapLegend />);
    expect(screen.queryByText(/clusters here/i)).not.toBeInTheDocument();
  });
});

import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MapLegend } from "./MapLegend";

describe("MapLegend", () => {
  it("is expanded by default and collapses when the toggle is clicked", () => {
    render(<MapLegend />);
    const toggle = screen.getByRole("button");
    expect(toggle).toHaveAttribute("aria-expanded", "true");
  });
});

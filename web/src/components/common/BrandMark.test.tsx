import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { BrandMark } from "./BrandMark";

describe("BrandMark", () => {
  it("renders an accessible SVG mark", () => {
    render(<BrandMark />);
    const mark = screen.getByTestId("brand-mark");
    expect(mark.tagName.toLowerCase()).toBe("svg");
    expect(mark).toHaveAttribute("role", "img");
    expect(mark).toHaveAttribute("aria-label", "apergia.map");
  });

  it("applies a custom size and className", () => {
    render(<BrandMark size={40} className="foo" />);
    const mark = screen.getByTestId("brand-mark");
    expect(mark).toHaveAttribute("width", "40");
    expect(mark).toHaveAttribute("height", "40");
    expect(mark).toHaveClass("foo");
  });
});

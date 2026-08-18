import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { AxisReferenceBlock } from "./AxisReferenceBlock";

describe("AxisReferenceBlock", () => {
  it("renders the label and children content", () => {
    render(
      <AxisReferenceBlock label="Action Form">
        <span>Occupation</span>
      </AxisReferenceBlock>,
    );
    expect(screen.getByText("Action Form")).toBeInTheDocument();
    expect(screen.getByText("Occupation")).toBeInTheDocument();
  });

  it("applies the given color as the block's border color", () => {
    const { container } = render(
      <AxisReferenceBlock label="Action Form" color="#2451c9">
        <span>Occupation</span>
      </AxisReferenceBlock>,
    );
    expect(container.firstElementChild).toHaveStyle({ borderColor: "#2451c9" });
  });

  it("falls back to no inline border color when none is given", () => {
    const { container } = render(
      <AxisReferenceBlock label="Intensity">
        <span>Peaceful</span>
      </AxisReferenceBlock>,
    );
    expect((container.firstElementChild as HTMLElement).style.borderColor).toBe("");
  });
});

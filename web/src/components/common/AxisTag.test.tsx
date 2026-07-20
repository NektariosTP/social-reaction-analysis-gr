import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { AxisTag } from "./AxisTag";

describe("AxisTag channel variant", () => {
  it("renders a solid border for the physical (offline) channel", () => {
    render(<AxisTag value="Φυσικό (offline)" variant="channel" />);
    expect(screen.getByText("Physical (offline)")).toHaveStyle({ borderStyle: "solid" });
  });

  it("renders a dashed border for the hybrid channel", () => {
    render(<AxisTag value="Υβριδικό" variant="channel" />);
    expect(screen.getByText("Hybrid")).toHaveStyle({ borderStyle: "dashed" });
  });

  it("renders a dotted border for the digital (online) channel", () => {
    render(<AxisTag value="Ψηφιακό (online)" variant="channel" />);
    expect(screen.getByText("Digital (online)")).toHaveStyle({ borderStyle: "dotted" });
  });
});

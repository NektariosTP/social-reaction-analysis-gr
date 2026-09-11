import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { AxisTag } from "./AxisTag";

describe("AxisTag", () => {
  it("renders each axis as a uniform pill differentiated by its variant class", () => {
    const { rerender } = render(<AxisTag value="Κατάληψη" variant="action" />);
    expect(screen.getByText("Occupation").className).toMatch(/action/);

    rerender(<AxisTag value="Εκπαίδευση" variant="theme" />);
    expect(screen.getByText("Education").className).toMatch(/theme/);

    rerender(<AxisTag value="Ψηφιακό (online)" variant="channel" />);
    expect(screen.getByText("Digital (online)").className).toMatch(/channel/);

    rerender(<AxisTag value="Βίαιη/Συγκρουσιακή" variant="intensity" />);
    expect(screen.getByText("Violent / Confrontational").className).toMatch(/intensity/);
  });
});

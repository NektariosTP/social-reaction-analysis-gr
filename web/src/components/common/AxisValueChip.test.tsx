import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { AxisValueChip } from "./AxisValueChip";

describe("AxisValueChip", () => {
  it("renders the action-form icon alongside the label", () => {
    render(<AxisValueChip axis="action" value="Κατάληψη" />);
    expect(screen.getByText("Occupation")).toBeInTheDocument();
    expect(screen.getByText("🏛")).toBeInTheDocument();
  });

  it("renders channel values as uniform pills (channel variant class)", () => {
    render(<AxisValueChip axis="channel" value="Ψηφιακό (online)" />);
    expect(screen.getByText("Digital (online)").className).toMatch(/channel/);
  });

  it("renders intensity values as uniform pills (intensity variant class)", () => {
    render(<AxisValueChip axis="intensity" value="Βίαιη/Συγκρουσιακή" />);
    expect(screen.getByText("Violent / Confrontational").className).toMatch(/intensity/);
  });

  it("renders a plain pill for thematic field values", () => {
    render(<AxisValueChip axis="theme" value="Εκπαίδευση" />);
    expect(screen.getByText("Education")).toBeInTheDocument();
  });
});

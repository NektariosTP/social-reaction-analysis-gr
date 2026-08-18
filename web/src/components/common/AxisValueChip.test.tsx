import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { AxisValueChip } from "./AxisValueChip";

describe("AxisValueChip", () => {
  it("renders the action-form icon alongside the label", () => {
    render(<AxisValueChip axis="action" value="Κατάληψη" />);
    expect(screen.getByText("Occupation")).toBeInTheDocument();
    expect(screen.getByText("🏛")).toBeInTheDocument();
  });

  it("renders the channel border style matching the map marker encoding", () => {
    render(<AxisValueChip axis="channel" value="Ψηφιακό (online)" />);
    expect(screen.getByText("Digital (online)")).toHaveStyle({ borderStyle: "dotted" });
  });

  it("renders the intensity background color matching the map marker encoding", () => {
    render(<AxisValueChip axis="intensity" value="Βίαιη/Συγκρουσιακή" />);
    expect(screen.getByText("Violent / Confrontational")).toHaveStyle({ background: "#c23b3b" });
  });

  it("renders a plain outline chip for thematic field values", () => {
    render(<AxisValueChip axis="theme" value="Εκπαίδευση" />);
    expect(screen.getByText("Education")).toBeInTheDocument();
  });
});

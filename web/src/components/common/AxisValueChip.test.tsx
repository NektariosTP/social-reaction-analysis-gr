import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
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

  it("renders a button and fires onToggle when interactive", async () => {
    const onToggle = vi.fn();
    render(<AxisValueChip axis="theme" value="Εργασιακό" onToggle={onToggle} active />);
    const btn = screen.getByRole("button");
    expect(btn).toHaveAttribute("aria-pressed", "true");
    await userEvent.click(btn);
    expect(onToggle).toHaveBeenCalledOnce();
  });

  it("stays a non-interactive span without onToggle", () => {
    const { container } = render(<AxisValueChip axis="theme" value="Εργασιακό" />);
    expect(container.querySelector("button")).toBeNull();
  });
});

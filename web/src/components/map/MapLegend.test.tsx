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

  it("also renders the thematic field axis (previously missing from the legend)", () => {
    render(<MapLegend />);
    expect(screen.getByText("Labour")).toBeInTheDocument();
  });

  it("renders the four axes in Action, Thematic, Channel, Intensity order", () => {
    const { container } = render(<MapLegend />);
    // One distinctive value per axis, reusing strings already asserted elsewhere in this file:
    // "Occupation" (axis1), "Labour" (axis2), "Digital (online)" (axis3), "Peaceful" (axis4).
    const text = container.textContent ?? "";
    const actionIdx = text.indexOf("Occupation");
    const thematicIdx = text.indexOf("Labour");
    const channelIdx = text.indexOf("Digital (online)");
    const intensityIdx = text.indexOf("Peaceful");
    expect(actionIdx).toBeGreaterThanOrEqual(0);
    expect(actionIdx).toBeLessThan(thematicIdx);
    expect(thematicIdx).toBeLessThan(channelIdx);
    expect(channelIdx).toBeLessThan(intensityIdx);
  });

  it("renders Thematic Field as plain rows, not AxisValueChip pills", () => {
    render(<MapLegend />);
    // AxisValueChip renders `<span class="chip theme">` (see AxisValueChip.tsx) — after the
    // fix, Thematic values render as `.row` divs (swatch + label) like the other three axes.
    const labourEl = screen.getByText("Labour");
    expect(labourEl.closest('[class*="chip"]')).toBeNull();
    expect(labourEl.closest('[class*="row"]')).not.toBeNull();
  });
});

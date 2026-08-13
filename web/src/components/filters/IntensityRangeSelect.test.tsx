import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { useState } from "react";
import { IntensityRangeSelect } from "./IntensityRangeSelect";

function StatefulHarness() {
  const [intensities, setIntensities] = useState<string[]>([]);
  return (
    <IntensityRangeSelect
      selected={intensities}
      onSetFilters={(next) => {
        if (next.intensities) setIntensities(next.intensities);
      }}
    />
  );
}

describe("IntensityRangeSelect", () => {
  it("renders all three levels checked when selected is empty (the all-sentinel)", () => {
    render(<IntensityRangeSelect selected={[]} onSetFilters={vi.fn()} />);
    const boxes = screen.getAllByRole("checkbox");
    expect(boxes).toHaveLength(3);
    expect(boxes.every((b) => (b as HTMLInputElement).checked)).toBe(true);
  });

  it("unchecking one box from the all-sentinel keeps the other two selected in state", () => {
    const onSetFilters = vi.fn();
    render(<IntensityRangeSelect selected={[]} onSetFilters={onSetFilters} />);
    screen.getByLabelText(/disruptive/i).click();
    expect(onSetFilters).toHaveBeenCalledTimes(1);
    const [{ intensities }] = onSetFilters.mock.calls[0];
    expect(intensities).toHaveLength(2);
    expect(intensities).not.toContain("Διαταρακτική (μη βίαιη, παρεμποδιστική)");
  });

  it("re-checking the last unchecked box collapses selection back to the empty sentinel", () => {
    const onSetFilters = vi.fn();
    render(
      <IntensityRangeSelect
        selected={["Ειρηνική", "Βίαιη/Συγκρουσιακή"]}
        onSetFilters={onSetFilters}
      />,
    );
    screen.getByLabelText(/disruptive/i).click();
    expect(onSetFilters).toHaveBeenCalledWith({ intensities: [] });
  });

  it("unchecking all three boxes leaves all three unchecked, not snapped back to all-checked", () => {
    render(<StatefulHarness />);
    screen.getByLabelText(/^peaceful/i).click();
    screen.getByLabelText(/^disruptive/i).click();
    screen.getByLabelText(/^violent/i).click();

    const boxes = screen.getAllByRole("checkbox") as HTMLInputElement[];
    expect(boxes.every((b) => !b.checked)).toBe(true);
  });
});

import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { IntensityRangeSelect } from "./IntensityRangeSelect";

describe("IntensityRangeSelect", () => {
  it("highlights 'All' when nothing is selected", () => {
    render(<IntensityRangeSelect selected={null} onChange={vi.fn()} />);
    const all = screen.getByRole("button", { name: /all/i });
    expect(all.className).toMatch(/chipSelected/);
  });

  it("clicking a value selects only that value", () => {
    const onChange = vi.fn();
    render(<IntensityRangeSelect selected={null} onChange={onChange} />);
    screen.getByRole("button", { name: /^peaceful$/i }).click();
    expect(onChange).toHaveBeenCalledWith("Ειρηνική");
  });

  it("highlights the currently-selected value, not All", () => {
    render(<IntensityRangeSelect selected="Ειρηνική" onChange={vi.fn()} />);
    expect(screen.getByRole("button", { name: /^peaceful$/i }).className).toMatch(/chipSelected/);
    expect(screen.getByRole("button", { name: /all/i }).className).not.toMatch(/chipSelected/);
  });

  it("clicking 'All' clears the selection", () => {
    const onChange = vi.fn();
    render(<IntensityRangeSelect selected="Ειρηνική" onChange={onChange} />);
    screen.getByRole("button", { name: /all/i }).click();
    expect(onChange).toHaveBeenCalledWith(null);
  });
});

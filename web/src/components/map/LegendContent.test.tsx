import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { FilterState } from "../../hooks/useFilterState";
import { LegendContent } from "./LegendContent";

const EMPTY: FilterState = {
  actionForms: [],
  thematicFields: [],
  channel: null,
  intensities: [],
  day: null,
  windowDays: null,
};

describe("LegendContent intensity chips (interactive)", () => {
  it("clicking an intensity chip from the default state narrows to just that value", async () => {
    const onToggleFilterValue = vi.fn();
    render(
      <LegendContent filters={EMPTY} onToggleFilterValue={onToggleFilterValue} onSetFilters={vi.fn()} />,
    );
    await userEvent.click(screen.getByRole("button", { name: /^Peaceful$/ }));
    // Additive, matching the Action/Theme axes: routed through the same
    // toggleInList-backed handler, not the checkbox-style "all" sentinel.
    expect(onToggleFilterValue).toHaveBeenCalledWith("intensities", "Ειρηνική");
  });

  it("highlights only the intensities present in the active filter list", () => {
    render(
      <LegendContent
        filters={{ ...EMPTY, intensities: ["Ειρηνική"] }}
        onToggleFilterValue={vi.fn()}
        onSetFilters={vi.fn()}
      />,
    );
    expect(screen.getByRole("button", { name: /^Peaceful$/ })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: /Violent/ })).toHaveAttribute("aria-pressed", "false");
  });
});

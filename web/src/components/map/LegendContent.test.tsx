import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { FilterState } from "../../hooks/useFilterState";
import { LegendContent } from "./LegendContent";

const EMPTY: FilterState = {
  actionForms: [],
  thematicFields: [],
  channel: null,
  intensity: null,
  day: null,
  windowDays: null,
};

describe("LegendContent intensity chips (interactive)", () => {
  it("clicking an intensity chip selects that value, single-select like channel", async () => {
    const onSetFilters = vi.fn();
    render(
      <LegendContent filters={EMPTY} onToggleFilterValue={vi.fn()} onSetFilters={onSetFilters} />,
    );
    await userEvent.click(screen.getByRole("button", { name: /^Peaceful$/ }));
    expect(onSetFilters).toHaveBeenCalledWith({ intensity: "Ειρηνική" });
  });

  it("clicking the already-active intensity chip clears it back to All", async () => {
    const onSetFilters = vi.fn();
    render(
      <LegendContent
        filters={{ ...EMPTY, intensity: "Ειρηνική" }}
        onToggleFilterValue={vi.fn()}
        onSetFilters={onSetFilters}
      />,
    );
    await userEvent.click(screen.getByRole("button", { name: /^Peaceful$/ }));
    expect(onSetFilters).toHaveBeenCalledWith({ intensity: null });
  });

  it("highlights only the active intensity", () => {
    render(
      <LegendContent
        filters={{ ...EMPTY, intensity: "Ειρηνική" }}
        onToggleFilterValue={vi.fn()}
        onSetFilters={vi.fn()}
      />,
    );
    expect(screen.getByRole("button", { name: /^Peaceful$/ })).toHaveAttribute("aria-pressed", "true");
    expect(screen.getByRole("button", { name: /Violent/ })).toHaveAttribute("aria-pressed", "false");
  });
});

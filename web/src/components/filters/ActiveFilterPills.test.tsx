import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import type { FilterState } from "../../hooks/useFilterState";
import { ActiveFilterPills } from "./ActiveFilterPills";

const EMPTY: FilterState = {
  actionForms: [],
  thematicFields: [],
  channel: null,
  intensity: null,
  day: null,
  windowDays: null,
};

function renderPills(filters: FilterState, handlers = {}) {
  return render(
    <MemoryRouter>
      <ActiveFilterPills
        filters={filters}
        onToggleFilterValue={vi.fn()}
        onSetFilters={vi.fn()}
        {...handlers}
      />
    </MemoryRouter>,
  );
}

describe("ActiveFilterPills", () => {
  it("renders nothing when no filter narrows the view", () => {
    const { container } = renderPills(EMPTY);
    expect(container.firstChild).toBeNull();
  });

  it("renders a removable pill for an active thematic field", async () => {
    const onToggleFilterValue = vi.fn();
    renderPills({ ...EMPTY, thematicFields: ["Εργασιακό"] }, { onToggleFilterValue });
    const remove = screen.getByRole("button", { name: /Labour/ });
    await userEvent.click(remove);
    expect(onToggleFilterValue).toHaveBeenCalledWith("thematicFields", "Εργασιακό");
  });

  it("renders a removable pill for an active intensity", async () => {
    const onSetFilters = vi.fn();
    renderPills({ ...EMPTY, intensity: "Ειρηνική" }, { onSetFilters });
    const remove = screen.getByRole("button", { name: /Peaceful/ });
    await userEvent.click(remove);
    expect(onSetFilters).toHaveBeenCalledWith({ intensity: null });
  });

  it("renders a range pill and clears it", async () => {
    const onSetFilters = vi.fn();
    renderPills({ ...EMPTY, windowDays: 7 }, { onSetFilters });
    await userEvent.click(screen.getByRole("button", { name: /last 7 days/i }));
    expect(onSetFilters).toHaveBeenCalledWith({ windowDays: null, day: null });
  });

  it("colors an action-form pill like its legend chip", () => {
    renderPills({ ...EMPTY, actionForms: ["Κατάληψη"] });
    expect(screen.getByRole("button", { name: /occupation/i }).className).toMatch(/action/);
  });

  it("colors a theme pill like its legend chip", () => {
    renderPills({ ...EMPTY, thematicFields: ["Εργασιακό"] });
    expect(screen.getByRole("button", { name: /labour/i }).className).toMatch(/theme/);
  });

  it("colors a channel pill like its legend chip", () => {
    renderPills({ ...EMPTY, channel: "Φυσικό (offline)" });
    expect(screen.getByRole("button", { name: /physical/i }).className).toMatch(/channel/);
  });

  it("colors an intensity pill like its legend chip", () => {
    renderPills({ ...EMPTY, intensity: "Ειρηνική" });
    expect(screen.getByRole("button", { name: /peaceful/i }).className).toMatch(/intensity/);
  });

  it("does not apply an axis color class to the range pill", () => {
    renderPills({ ...EMPTY, windowDays: 7 });
    const className = screen.getByRole("button", { name: /last 7 days/i }).className;
    expect(className).not.toMatch(/action|theme|channel|intensity/);
  });
});

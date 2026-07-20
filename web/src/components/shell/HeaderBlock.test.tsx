import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { HeaderBlock } from "./HeaderBlock";
import type { FilterState } from "../../hooks/useFilterState";

const baseFilters: FilterState = {
  actionForms: [],
  thematicFields: [],
  channel: null,
  intensities: [],
  timeRange: "all",
};

function setup(overrides: Partial<React.ComponentProps<typeof HeaderBlock>> = {}) {
  const props = {
    searchQuery: "",
    onSearchChange: vi.fn(),
    onSelectRegion: vi.fn(),
    filters: baseFilters,
    onToggleFilterValue: vi.fn(),
    onSetFilters: vi.fn(),
    ...overrides,
  };
  render(<HeaderBlock {...props} />);
  return props;
}

describe("HeaderBlock", () => {
  beforeEach(() => sessionStorage.clear());

  it("expands the search panel with region shortcuts on focus", () => {
    setup();
    fireEvent.focus(screen.getByPlaceholderText(/search/i));
    expect(screen.getByText("Attica")).toBeInTheDocument();
  });

  it("calls onSelectRegion and collapses when a region shortcut is clicked", () => {
    const props = setup();
    fireEvent.focus(screen.getByPlaceholderText(/search/i));
    fireEvent.click(screen.getByText("Crete"));
    expect(props.onSelectRegion).toHaveBeenCalledWith(expect.objectContaining({ en: "Crete" }));
    expect(screen.queryByText("Attica")).not.toBeInTheDocument();
  });

  it("expands the filter panel and closes the search panel if it was open", () => {
    setup();
    fireEvent.focus(screen.getByPlaceholderText(/search/i));
    fireEvent.click(screen.getByText(/filters/i));
    expect(screen.queryByText("Attica")).not.toBeInTheDocument();
    expect(screen.getByText("Clear")).toBeInTheDocument();
  });

  it("calls onSetFilters with a fully-reset state when Clear is clicked", () => {
    const props = setup({
      filters: { ...baseFilters, actionForms: ["Κατάληψη"], timeRange: "7d" },
    });
    fireEvent.click(screen.getByText(/filters/i));
    fireEvent.click(screen.getByText("Clear"));
    expect(props.onSetFilters).toHaveBeenCalledWith({
      actionForms: [],
      thematicFields: [],
      channel: null,
      intensities: [],
      timeRange: "all",
    });
  });

  it("collapses the filter panel when Save is clicked", () => {
    setup();
    fireEvent.click(screen.getByText(/filters/i));
    fireEvent.click(screen.getByText("Save"));
    expect(screen.queryByText("Clear")).not.toBeInTheDocument();
  });
});

import { describe, expect, it, vi } from "vitest";
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
  it("shows the Browse by region option (not region chips directly) on search focus", () => {
    setup();
    fireEvent.focus(screen.getByPlaceholderText(/search/i));
    expect(screen.getByText("Browse by region")).toBeInTheDocument();
    expect(screen.queryByText("Attica")).not.toBeInTheDocument();
  });

  it("drills into region chips when Browse by region is clicked, with a back control", () => {
    setup();
    fireEvent.focus(screen.getByPlaceholderText(/search/i));
    fireEvent.click(screen.getByText("Browse by region"));
    expect(screen.getByText("Attica")).toBeInTheDocument();
    expect(screen.getByText("‹ Back")).toBeInTheDocument();
  });

  it("returns to the options list when Back is clicked", () => {
    setup();
    fireEvent.focus(screen.getByPlaceholderText(/search/i));
    fireEvent.click(screen.getByText("Browse by region"));
    fireEvent.click(screen.getByText("‹ Back"));
    expect(screen.getByText("Browse by region")).toBeInTheDocument();
    expect(screen.queryByText("Attica")).not.toBeInTheDocument();
  });

  it("calls onSelectRegion and collapses when a region shortcut is clicked", () => {
    const props = setup();
    fireEvent.focus(screen.getByPlaceholderText(/search/i));
    fireEvent.click(screen.getByText("Browse by region"));
    fireEvent.click(screen.getByText("Crete"));
    expect(props.onSelectRegion).toHaveBeenCalledWith(expect.objectContaining({ en: "Crete" }));
    expect(screen.queryByText("Attica")).not.toBeInTheDocument();
  });

  it("resets to the options view each time the search panel is reopened", () => {
    setup();
    fireEvent.focus(screen.getByPlaceholderText(/search/i));
    fireEvent.click(screen.getByText("Browse by region"));
    fireEvent.click(screen.getByText(/filters/i));
    fireEvent.focus(screen.getByPlaceholderText(/search/i));
    expect(screen.getByText("Browse by region")).toBeInTheDocument();
    expect(screen.queryByText("Attica")).not.toBeInTheDocument();
  });

  it("expands the filter panel and closes the search panel if it was open", () => {
    setup();
    fireEvent.focus(screen.getByPlaceholderText(/search/i));
    fireEvent.click(screen.getByText(/filters/i));
    expect(screen.queryByText("Browse by region")).not.toBeInTheDocument();
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

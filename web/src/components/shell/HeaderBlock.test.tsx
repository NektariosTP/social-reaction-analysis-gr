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
    filters: baseFilters,
    onToggleFilterValue: vi.fn(),
    onSetFilters: vi.fn(),
    ...overrides,
  };
  render(<HeaderBlock {...props} />);
  return props;
}

describe("HeaderBlock", () => {
  it("renders the SVG brand mark, not a letter mark", () => {
    setup();
    expect(screen.getByTestId("brand-mark")).toBeInTheDocument();
    expect(screen.queryByText("p")).not.toBeInTheDocument();
  });

  it("expands the filter panel and closes the search panel if it was open", () => {
    setup();
    fireEvent.focus(screen.getByPlaceholderText(/search/i));
    fireEvent.click(screen.getByText(/filters/i));
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

  it("closes the filter popup when clicking outside the header block", () => {
    render(
      <div>
        <div data-testid="outside">outside</div>
        <HeaderBlock
          searchQuery=""
          onSearchChange={vi.fn()}
          filters={baseFilters}
          onToggleFilterValue={vi.fn()}
          onSetFilters={vi.fn()}
        />
      </div>,
    );
    fireEvent.click(screen.getByText(/filters/i));
    expect(screen.getByText("Clear")).toBeInTheDocument();
    fireEvent.pointerDown(screen.getByTestId("outside"));
    expect(screen.queryByText("Clear")).not.toBeInTheDocument();
  });

  it("keeps the filter popup open when clicking inside it", () => {
    setup();
    fireEvent.click(screen.getByText(/filters/i));
    fireEvent.pointerDown(screen.getByText("Clear"));
    expect(screen.getByText("Clear")).toBeInTheDocument();
  });

  it("closes the popup on Escape", () => {
    setup();
    fireEvent.click(screen.getByText(/filters/i));
    expect(screen.getByText("Clear")).toBeInTheDocument();
    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByText("Clear")).not.toBeInTheDocument();
  });

  it("preserves the search query text when Escape closes the search popup", () => {
    const props = setup({ searchQuery: "athens" });
    fireEvent.focus(screen.getByPlaceholderText(/search/i));
    fireEvent.keyDown(document, { key: "Escape" });
    expect(props.onSearchChange).not.toHaveBeenCalled();
  });
});

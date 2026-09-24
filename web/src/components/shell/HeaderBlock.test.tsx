import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import "../../i18n";
import { HeaderBlock } from "./HeaderBlock";
import type { FilterState } from "../../hooks/useFilterState";

const baseFilters: FilterState = {
  actionForms: [],
  thematicFields: [],
  channel: null,
  intensities: [],
  day: null,
  windowDays: null,
};

function setup(overrides: Partial<React.ComponentProps<typeof HeaderBlock>> = {}) {
  const props = {
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
  });

  it("renders the range selector instead of a search input", () => {
    setup();
    expect(screen.getByRole("button", { name: /live/i })).toBeInTheDocument();
    expect(screen.queryByPlaceholderText(/search/i)).not.toBeInTheDocument();
  });

  it("expands the filter panel when the Filters toggle is clicked", () => {
    setup();
    fireEvent.click(screen.getByText(/filters/i));
    expect(screen.getByText("Clear")).toBeInTheDocument();
  });

  it("calls onSetFilters with a fully-reset state (day → null) when Clear is clicked", () => {
    const props = setup({
      filters: { ...baseFilters, actionForms: ["Κατάληψη"], day: "2026-09-09" },
    });
    fireEvent.click(screen.getByText(/filters/i));
    fireEvent.click(screen.getByText("Clear"));
    expect(props.onSetFilters).toHaveBeenCalledWith({
      actionForms: [],
      thematicFields: [],
      channel: null,
      intensities: [],
      day: null,
      windowDays: null,
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
        <HeaderBlock filters={baseFilters} onToggleFilterValue={vi.fn()} onSetFilters={vi.fn()} />
      </div>,
    );
    fireEvent.click(screen.getByText(/filters/i));
    expect(screen.getByText("Clear")).toBeInTheDocument();
    fireEvent.pointerDown(screen.getByTestId("outside"));
    expect(screen.queryByText("Clear")).not.toBeInTheDocument();
  });

  it("closes the popup on Escape", () => {
    setup();
    fireEvent.click(screen.getByText(/filters/i));
    expect(screen.getByText("Clear")).toBeInTheDocument();
    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByText("Clear")).not.toBeInTheDocument();
  });

  it("renders the trailing slot in the brand row", () => {
    setup({ trailing: <button>EL</button> });
    expect(screen.getByRole("button", { name: "EL" })).toBeInTheDocument();
  });
});

import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import "../../i18n";
import { HeaderBlock } from "./HeaderBlock";
import type { FilterState } from "../../hooks/useFilterState";

const baseFilters: FilterState = {
  actionForms: [],
  thematicFields: [],
  channel: null,
  intensity: null,
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
      intensity: null,
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

  it("expands the range panel in the same slot as the filter panel, inline (not a floating dropdown)", () => {
    setup();
    fireEvent.click(screen.getByRole("button", { name: /live/i }));
    expect(screen.getByRole("button", { name: /last 7 days/i })).toBeInTheDocument();
  });

  it("opening the range panel closes an already-open filter panel, and vice versa", () => {
    setup();
    fireEvent.click(screen.getByText(/filters/i));
    expect(screen.getByText("Clear")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /live/i }));
    expect(screen.queryByText("Clear")).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /last 7 days/i })).toBeInTheDocument();

    fireEvent.click(screen.getByText(/filters/i));
    expect(screen.queryByRole("button", { name: /last 7 days/i })).not.toBeInTheDocument();
    expect(screen.getByText("Clear")).toBeInTheDocument();
  });

  it("picking a preset updates filters without closing the range panel; Save closes it", () => {
    const props = setup();
    fireEvent.click(screen.getByRole("button", { name: /live/i }));
    fireEvent.click(screen.getByRole("button", { name: /last 15 days/i }));
    expect(props.onSetFilters).toHaveBeenCalledWith({ windowDays: 15, day: null });
    expect(screen.getByRole("button", { name: /last 15 days/i })).toBeInTheDocument();

    fireEvent.click(screen.getByText("Save"));
    expect(screen.queryByRole("button", { name: /last 15 days/i })).not.toBeInTheDocument();
  });
});

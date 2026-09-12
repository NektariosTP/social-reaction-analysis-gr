import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { BottomSheet } from "./BottomSheet";

function setup(activePanel = 0, onChange = vi.fn()) {
  render(
    <BottomSheet
      panels={[<div key="a">Panel A</div>, <div key="b">Panel B</div>]}
      activePanel={activePanel}
      onActivePanelChange={onChange}
      footer={<div>footer row</div>}
    />,
  );
  return { onChange };
}

describe("BottomSheet", () => {
  it("renders one panel and one dot per panel, plus a handle and footer", () => {
    setup();
    expect(screen.getAllByTestId("sheet-panel")).toHaveLength(2);
    expect(screen.getAllByTestId("sheet-dot")).toHaveLength(2);
    expect(screen.getByTestId("sheet-handle")).toBeInTheDocument();
    expect(screen.getByText("footer row")).toBeInTheDocument();
    expect(screen.getByText("Panel A")).toBeInTheDocument();
    expect(screen.getByText("Panel B")).toBeInTheDocument();
  });

  it("marks the active dot", () => {
    setup(1);
    const dots = screen.getAllByTestId("sheet-dot");
    expect(dots[1]).toHaveAttribute("data-active", "true");
    expect(dots[0]).not.toHaveAttribute("data-active", "true");
  });

  it("toggles expanded state when the handle is clicked", () => {
    setup();
    const sheet = screen.getByTestId("bottom-sheet");
    const handle = screen.getByTestId("sheet-handle");
    expect(sheet).toHaveAttribute("data-expanded", "false");
    fireEvent.click(handle);
    expect(sheet).toHaveAttribute("data-expanded", "true");
  });
});

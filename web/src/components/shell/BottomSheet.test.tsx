import { describe, expect, it } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { BottomSheet } from "./BottomSheet";

describe("BottomSheet", () => {
  it("renders its children inside the sheet, plus a drag handle", () => {
    render(
      <BottomSheet bottomOffset={56}>
        <div>Panel content</div>
      </BottomSheet>,
    );
    expect(screen.getByTestId("sheet-handle")).toBeInTheDocument();
    expect(screen.getByText("Panel content")).toBeInTheDocument();
  });

  it("offsets the sheet's bottom edge by bottomOffset", () => {
    render(
      <BottomSheet bottomOffset={56}>
        <div>Panel content</div>
      </BottomSheet>,
    );
    expect(screen.getByTestId("bottom-sheet")).toHaveStyle({ bottom: "56px" });
  });

  it("toggles expanded state when the handle is clicked", () => {
    render(
      <BottomSheet bottomOffset={56}>
        <div>Panel content</div>
      </BottomSheet>,
    );
    const sheet = screen.getByTestId("bottom-sheet");
    const handle = screen.getByTestId("sheet-handle");
    expect(sheet).toHaveAttribute("data-expanded", "false");
    fireEvent.click(handle);
    expect(sheet).toHaveAttribute("data-expanded", "true");
  });
});

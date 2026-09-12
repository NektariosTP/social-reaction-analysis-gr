import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { BottomNav } from "./BottomNav";

describe("BottomNav", () => {
  it("renders one button per tab with the active one flagged", () => {
    render(<BottomNav active="feed" onChange={vi.fn()} />);
    const buttons = screen.getAllByRole("button");
    expect(buttons).toHaveLength(4);
    expect(screen.getByText("Feed").closest("button")).toHaveAttribute("data-active", "true");
    expect(screen.getByText("Calendar").closest("button")).not.toHaveAttribute("data-active", "true");
  });

  it("calls onChange with the tapped tab's key", () => {
    const onChange = vi.fn();
    render(<BottomNav active="temporal" onChange={onChange} />);
    fireEvent.click(screen.getByText("Legend").closest("button")!);
    expect(onChange).toHaveBeenCalledWith("legend");
  });
});

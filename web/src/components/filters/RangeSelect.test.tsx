import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { RangeSelect } from "./RangeSelect";

describe("RangeSelect (trigger)", () => {
  it("shows Live by default and calls onClick when pressed", async () => {
    const onClick = vi.fn();
    render(<RangeSelect windowDays={null} day={null} open={false} onClick={onClick} />);
    const trigger = screen.getByRole("button", { name: /live/i });
    expect(trigger).toHaveAttribute("aria-expanded", "false");
    await userEvent.click(trigger);
    expect(onClick).toHaveBeenCalledOnce();
  });

  it("shows the preset label when a window is active", () => {
    render(<RangeSelect windowDays={7} day={null} open onClick={vi.fn()} />);
    expect(screen.getByRole("button", { name: /last 7 days/i })).toHaveAttribute("aria-expanded", "true");
  });

  it("shows the formatted date when an exact day is active", () => {
    render(<RangeSelect windowDays={null} day="2026-09-18" open={false} onClick={vi.fn()} />);
    expect(screen.getByRole("button", { name: /2026/ })).toBeInTheDocument();
  });
});

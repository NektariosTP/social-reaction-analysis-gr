import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { RangePanel } from "./RangePanel";

describe("RangePanel", () => {
  it("emits a preset on selection", async () => {
    const onChange = vi.fn();
    render(<RangePanel windowDays={null} day={null} onChange={onChange} />);
    await userEvent.click(screen.getByRole("button", { name: /last 7 days/i }));
    expect(onChange).toHaveBeenCalledWith({ windowDays: 7, day: null });
  });

  it("emits Live (both null) when the Live row is clicked", async () => {
    const onChange = vi.fn();
    render(<RangePanel windowDays={7} day={null} onChange={onChange} />);
    await userEvent.click(screen.getByRole("button", { name: /live/i }));
    expect(onChange).toHaveBeenCalledWith({ windowDays: null, day: null });
  });

  it("marks the active preset", () => {
    render(<RangePanel windowDays={15} day={null} onChange={vi.fn()} />);
    expect(screen.getByRole("button", { name: /last 15 days/i })).toHaveAttribute("data-active");
    expect(screen.getByRole("button", { name: /last 7 days/i })).not.toHaveAttribute("data-active");
  });

  it("emits an exact day from the date input", async () => {
    const onChange = vi.fn();
    render(<RangePanel windowDays={null} day={null} onChange={onChange} />);
    const input = screen.getByLabelText(/select exact date/i);
    await userEvent.type(input, "2026-09-18");
    expect(onChange).toHaveBeenLastCalledWith({ windowDays: null, day: "2026-09-18" });
  });
});

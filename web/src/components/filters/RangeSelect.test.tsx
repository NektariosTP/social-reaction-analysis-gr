import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { RangeSelect } from "./RangeSelect";

describe("RangeSelect", () => {
  it("shows Live by default and emits a preset on selection", async () => {
    const onChange = vi.fn();
    render(<RangeSelect windowDays={null} day={null} onChange={onChange} />);
    expect(screen.getByRole("button", { name: /live/i })).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /live/i }));
    await userEvent.click(screen.getByRole("button", { name: /last 7 days/i }));
    expect(onChange).toHaveBeenCalledWith({ windowDays: 7, day: null });
  });

  it("emits an exact day from the date input", async () => {
    const onChange = vi.fn();
    render(<RangeSelect windowDays={null} day={null} onChange={onChange} />);
    await userEvent.click(screen.getByRole("button", { name: /live/i }));
    const input = screen.getByLabelText(/select exact date/i);
    await userEvent.type(input, "2026-09-18");
    expect(onChange).toHaveBeenLastCalledWith({ windowDays: null, day: "2026-09-18" });
  });
});

import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import "../../i18n";
import { TimelineSlider } from "./TimelineSlider";

function isoNDaysAgo(n: number): string {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  d.setDate(d.getDate() - n);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function formatIso(iso: string): string {
  const [y, m, d] = iso.split("-").map(Number);
  return new Intl.DateTimeFormat("en", { day: "numeric", month: "short", year: "numeric" }).format(
    new Date(y, m - 1, d),
  );
}

describe("TimelineSlider", () => {
  it("shows today's date (never the word Live) and sits at the rightmost position when value is null", () => {
    render(<TimelineSlider value={null} onChange={vi.fn()} maxDaysBack={30} />);
    expect(screen.getByText(formatIso(isoNDaysAgo(0)))).toBeInTheDocument();
    expect(screen.queryByText("Live")).not.toBeInTheDocument();
    const input = screen.getByRole("slider") as HTMLInputElement;
    expect(input.value).toBe("30");
  });

  it("positions the thumb by days-back for a past day", () => {
    render(<TimelineSlider value={isoNDaysAgo(5)} onChange={vi.fn()} maxDaysBack={30} />);
    const input = screen.getByRole("slider") as HTMLInputElement;
    expect(input.value).toBe("25"); // 30 - 5 days back
    expect(screen.getByText(formatIso(isoNDaysAgo(5)))).toBeInTheDocument();
  });

  it("updates the label live on input but does NOT commit onChange until release", () => {
    const onChange = vi.fn();
    render(<TimelineSlider value={null} onChange={onChange} maxDaysBack={30} />);
    const input = screen.getByRole("slider") as HTMLInputElement;
    fireEvent.input(input, { target: { value: "20" } }); // 10 days back
    expect(onChange).not.toHaveBeenCalled();
    expect(screen.getByText(formatIso(isoNDaysAgo(10)))).toBeInTheDocument();
  });

  it("commits the resolved day on release (change event)", () => {
    const onChange = vi.fn();
    render(<TimelineSlider value={null} onChange={onChange} maxDaysBack={30} />);
    const input = screen.getByRole("slider") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "20" } }); // 10 days back
    expect(onChange).toHaveBeenCalledWith(isoNDaysAgo(10));
  });

  it("commits null (Live) when released at the rightmost position", () => {
    const onChange = vi.fn();
    render(<TimelineSlider value={isoNDaysAgo(3)} onChange={onChange} maxDaysBack={30} />);
    const input = screen.getByRole("slider") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "30" } });
    expect(onChange).toHaveBeenCalledWith(null);
  });
});

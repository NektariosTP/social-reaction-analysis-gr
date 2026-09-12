import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MapLegend } from "./MapLegend";

vi.mock("../../hooks/useIsMobile", () => ({ useIsMobile: vi.fn() }));
import { useIsMobile } from "../../hooks/useIsMobile";

describe("MapLegend", () => {
  beforeEach(() => vi.clearAllMocks());

  it("is collapsed by default on mobile", () => {
    (useIsMobile as unknown as ReturnType<typeof vi.fn>).mockReturnValue(true);
    render(<MapLegend />);
    const toggle = screen.getByRole("button");
    expect(toggle).toHaveAttribute("aria-expanded", "false");
  });

  it("is expanded by default on desktop", () => {
    (useIsMobile as unknown as ReturnType<typeof vi.fn>).mockReturnValue(false);
    render(<MapLegend />);
    const toggle = screen.getByRole("button");
    expect(toggle).toHaveAttribute("aria-expanded", "true");
  });
});

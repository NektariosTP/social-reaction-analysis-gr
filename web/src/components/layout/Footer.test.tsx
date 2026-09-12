// web/src/components/layout/Footer.test.tsx
import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Footer } from "./Footer";

describe("Footer", () => {
  it("renders GitHub and Contact links", () => {
    render(<Footer />);
    expect(screen.getByText("GitHub")).toHaveAttribute(
      "href",
      "https://github.com/NektariosTP/social-reaction-analysis-gr",
    );
    expect(screen.getByText("Contact")).toHaveAttribute("href", "mailto:nektarios.tp@gmail.com");
    expect(screen.queryByText("Docs")).not.toBeInTheDocument();
    expect(screen.queryByText("Privacy Policy")).not.toBeInTheDocument();
  });

  it("renders an About button that opens the About modal via callback", () => {
    const onAbout = vi.fn();
    render(<Footer onAbout={onAbout} />);
    fireEvent.click(screen.getByRole("button", { name: "About" }));
    expect(onAbout).toHaveBeenCalled();
  });
});

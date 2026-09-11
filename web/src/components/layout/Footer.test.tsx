// web/src/components/layout/Footer.test.tsx
import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Footer } from "./Footer";

describe("Footer", () => {
  it("renders Docs, GitHub, Contact, and Privacy Policy links", () => {
    render(<Footer />);
    expect(screen.getByText("Docs")).toBeInTheDocument();
    expect(screen.getByText("GitHub")).toHaveAttribute(
      "href",
      "https://github.com/NektariosTP/social-reaction-analysis-gr",
    );
    expect(screen.getByText("Contact")).toHaveAttribute("href", "mailto:nektarios.tp@gmail.com");
    expect(screen.getByText("Privacy Policy")).toBeInTheDocument();
  });

  it("renders an About button that opens the About modal via callback", () => {
    const onAbout = vi.fn();
    render(<Footer onAbout={onAbout} />);
    fireEvent.click(screen.getByRole("button", { name: "About" }));
    expect(onAbout).toHaveBeenCalled();
  });
});

// web/src/components/layout/Footer.test.tsx
import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { Footer } from "./Footer";

describe("Footer", () => {
  it("renders About, Docs, GitHub, Contact, and Privacy Policy links", () => {
    render(
      <MemoryRouter>
        <Footer />
      </MemoryRouter>,
    );
    expect(screen.getByText("About")).toHaveAttribute("href", "/about");
    expect(screen.getByText("Docs")).toBeInTheDocument();
    expect(screen.getByText("GitHub")).toHaveAttribute(
      "href",
      "https://github.com/NektariosTP/social-reaction-analysis-gr",
    );
    expect(screen.getByText("Contact")).toHaveAttribute("href", "mailto:nektarios.tp@gmail.com");
    expect(screen.getByText("Privacy Policy")).toBeInTheDocument();
  });
});

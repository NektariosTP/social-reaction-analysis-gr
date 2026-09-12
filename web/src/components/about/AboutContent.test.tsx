import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { AboutContent } from "./AboutContent";

describe("AboutContent", () => {
  it("links to the real GitHub repository and contact email, not placeholders", () => {
    render(<AboutContent />);
    expect(screen.getByText("GitHub repository").closest("a")).toHaveAttribute(
      "href",
      "https://github.com/NektariosTP/social-reaction-analysis-gr",
    );
    expect(screen.getByText("Contact / feedback").closest("a")).toHaveAttribute(
      "href",
      "mailto:nektarios.tp@gmail.com",
    );
  });
});

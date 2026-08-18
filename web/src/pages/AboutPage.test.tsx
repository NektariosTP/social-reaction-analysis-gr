import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AboutPage } from "./AboutPage";

function renderAboutPage() {
  const queryClient = new QueryClient();
  render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <AboutPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

describe("AboutPage", () => {
  it("renders each thematic-field value as its own chip instead of a joined string", () => {
    renderAboutPage();
    expect(screen.getByText("Labour")).toBeInTheDocument();
    expect(screen.getByText("Police violence")).toBeInTheDocument();
  });

  it("renders the channel chips with their real border style", () => {
    renderAboutPage();
    expect(screen.getByText("Physical (offline)")).toHaveStyle({ borderStyle: "solid" });
  });
});

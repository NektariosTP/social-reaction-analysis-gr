import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AppShell } from "./AppShell";

describe("AppShell", () => {
  it("centers content with a max-width and side padding", () => {
    render(
      <MemoryRouter>
        <AppShell>
          <div>page content</div>
        </AppShell>
      </MemoryRouter>,
    );
    const main = screen.getByText("page content").closest("main");
    expect(main).toHaveStyle({ maxWidth: "1200px", marginLeft: "auto", marginRight: "auto" });
  });
});

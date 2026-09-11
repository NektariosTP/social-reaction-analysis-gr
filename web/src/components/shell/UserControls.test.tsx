import { describe, expect, it } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import i18n from "../../i18n";
import { UserControls } from "./UserControls";

describe("UserControls", () => {
  it("renders the EL/EN language switch", () => {
    render(<UserControls />);
    expect(screen.getByRole("button", { name: "EL" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "EN" })).toBeInTheDocument();
  });

  it("switches the active language when a button is clicked", async () => {
    await i18n.changeLanguage("en");
    render(<UserControls />);
    fireEvent.click(screen.getByRole("button", { name: "EL" }));
    expect(screen.getByRole("button", { name: "EL" })).toHaveAttribute("aria-pressed", "true");
    await i18n.changeLanguage("en");
  });
});

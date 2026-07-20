import { describe, expect, it } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { UserControls } from "./UserControls";

describe("UserControls", () => {
  it("shows a coming-soon placeholder when Login is opened", () => {
    render(<UserControls />);
    fireEvent.click(screen.getByRole("button", { name: /login/i }));
    expect(screen.getByText("Coming soon")).toBeInTheDocument();
  });

  it("shows the language toggle when Settings is opened", () => {
    render(<UserControls />);
    fireEvent.click(screen.getByRole("button", { name: /settings/i }));
    expect(screen.getByText("Language")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "EL" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "EN" })).toBeInTheDocument();
  });

  it("only shows one panel at a time", () => {
    render(<UserControls />);
    fireEvent.click(screen.getByRole("button", { name: /login/i }));
    fireEvent.click(screen.getByRole("button", { name: /settings/i }));
    expect(screen.queryByText("Coming soon")).not.toBeInTheDocument();
    expect(screen.getByText("Language")).toBeInTheDocument();
  });
});

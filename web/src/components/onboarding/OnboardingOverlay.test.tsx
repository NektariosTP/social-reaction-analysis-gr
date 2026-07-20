import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { OnboardingOverlay } from "./OnboardingOverlay";

describe("OnboardingOverlay", () => {
  it("renders each action-form value as its own chip", () => {
    render(
      <MemoryRouter>
        <OnboardingOverlay onDismiss={() => {}} />
      </MemoryRouter>,
    );
    expect(screen.getByText("Demonstration / March / Rally")).toBeInTheDocument();
    expect(screen.getByText("Strike / Work stoppage")).toBeInTheDocument();
  });

  it("does not join action-form values with a middle-dot separator", () => {
    render(
      <MemoryRouter>
        <OnboardingOverlay onDismiss={() => {}} />
      </MemoryRouter>,
    );
    expect(screen.getByTestId("axis-action-values").textContent).not.toContain("·");
  });

  it("renders the channel chips with their real border style", () => {
    render(
      <MemoryRouter>
        <OnboardingOverlay onDismiss={() => {}} />
      </MemoryRouter>,
    );
    expect(screen.getByText("Digital (online)")).toHaveStyle({ borderStyle: "dotted" });
  });
});

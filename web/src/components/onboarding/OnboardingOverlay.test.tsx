import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
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

  it("uses plain copy without 'axes' or 'social media' jargon", () => {
    render(
      <MemoryRouter>
        <OnboardingOverlay onDismiss={() => {}} />
      </MemoryRouter>,
    );
    expect(screen.getByText("What we track for every event")).toBeInTheDocument();
    expect(document.body.textContent).not.toMatch(/axes|axis/i);
    expect(document.body.textContent).not.toMatch(/social media/i);
  });

  it("calls onMethodology when the methodology button is clicked", () => {
    const onMethodology = vi.fn();
    render(
      <MemoryRouter>
        <OnboardingOverlay onDismiss={() => {}} onMethodology={onMethodology} />
      </MemoryRouter>,
    );
    fireEvent.click(screen.getByText(/methodology/i));
    expect(onMethodology).toHaveBeenCalled();
  });
});

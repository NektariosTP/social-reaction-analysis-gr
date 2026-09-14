import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { SourceEvidenceList } from "./SourceEvidenceList";

describe("SourceEvidenceList", () => {
  it("shows the empty state when there are no articles and no reactions", () => {
    render(<SourceEvidenceList articles={[]} reactions={[]} />);
    expect(screen.getByText(/no sources recorded/i)).toBeInTheDocument();
  });

  it("renders a union announcement as a valid source when there are no articles", () => {
    render(
      <SourceEvidenceList
        articles={[]}
        reactions={[
          {
            id: "r1", actor_name: "ΑΔΕΔΥ", source_org: "adedy",
            url: "https://adedy.gr/stasiergasias1692026/", observed_at: null,
            text: "Στάση εργασίας 16 Σεπτεμβρίου",
          },
        ]}
      />,
    );
    expect(screen.getByText("ΑΔΕΔΥ")).toBeInTheDocument();
    expect(screen.getByText("Στάση εργασίας 16 Σεπτεμβρίου")).toBeInTheDocument();
    expect(screen.getByText("ΑΔΕΔΥ").closest("a")).toHaveAttribute(
      "href", "https://adedy.gr/stasiergasias1692026/",
    );
    expect(screen.queryByText(/no sources recorded/i)).not.toBeInTheDocument();
  });

  it("combines articles and reactions into one source list", () => {
    render(
      <SourceEvidenceList
        articles={[
          { id: "a1", source_id: "in.gr", source_type: "news", url: "http://in.gr/1",
            title: "Απεργία αύριο", published_at: null },
        ]}
        reactions={[
          { id: "r1", actor_name: "ΠΑΜΕ", source_org: "pame",
            url: "http://pame/1", observed_at: null, text: "Ανακοίνωση" },
        ]}
      />,
    );
    expect(screen.getByText("in.gr")).toBeInTheDocument();
    expect(screen.getByText("ΠΑΜΕ")).toBeInTheDocument();
  });
});

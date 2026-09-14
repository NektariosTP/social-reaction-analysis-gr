import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { UnionSourceList } from "./UnionSourceList";

describe("UnionSourceList", () => {
  it("renders nothing when there are no reactions", () => {
    const { container } = render(<UnionSourceList reactions={[]} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("shows the first reaction as announcer and the rest as supporters, with links", () => {
    render(
      <UnionSourceList
        reactions={[
          { id: "1", actor_name: "ΑΔΕΔΥ", source_org: "adedy", url: "http://adedy/1", observed_at: null, text: null },
          { id: "2", actor_name: "ΠΑΜΕ", source_org: "pame", url: "http://pame/1", observed_at: null, text: null },
        ]}
      />,
    );
    const announcer = screen.getByText("ΑΔΕΔΥ").closest("a");
    expect(announcer).toHaveAttribute("href", "http://adedy/1");
    expect(screen.getByText("ΠΑΜΕ").closest("a")).toHaveAttribute("href", "http://pame/1");
  });

  it("does not list the announcing union again as a supporter of its own announcement", () => {
    // The announcer can have a second event_reactions row (e.g. a later
    // 'deduped' article about the same rally). It must not double-list itself.
    render(
      <UnionSourceList
        reactions={[
          { id: "1", actor_name: "ΠΑΜΕ", source_org: "pame", url: "http://pame/seeded", observed_at: null, text: null },
          { id: "2", actor_name: "ΠΑΜΕ", source_org: "pame", url: "http://pame/deduped", observed_at: null, text: null },
          { id: "3", actor_name: "ΑΔΕΔΥ", source_org: "adedy", url: "http://adedy/1", observed_at: null, text: null },
        ]}
      />,
    );
    expect(screen.getAllByText("ΠΑΜΕ")).toHaveLength(1);
    expect(screen.getByText("ΠΑΜΕ").closest("a")).toHaveAttribute("href", "http://pame/seeded");
    expect(screen.getByText("ΑΔΕΔΥ").closest("a")).toHaveAttribute("href", "http://adedy/1");
  });
});

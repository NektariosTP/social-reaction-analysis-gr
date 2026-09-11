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
});

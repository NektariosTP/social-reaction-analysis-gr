import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { ClassificationTable } from "./ClassificationTable";
import type { EventDetail } from "../../client/types.gen";

const event = {
  id: "evt-1",
  action_forms: ["Κατάληψη"],
  thematic_fields: ["Εργασιακό"],
  channel: "Φυσικό",
  intensity: "Ειρηνική",
  classification_confidence: null,
} as unknown as EventDetail;

describe("ClassificationTable", () => {
  it("renders axis names and tags without Conf./Axis/Labels headers", () => {
    render(<ClassificationTable event={event} />);
    // translated axis name (en): "Action"
    expect(screen.getByText("Action")).toBeInTheDocument();
    // no header/jargon text
    expect(screen.queryByText("Conf.")).not.toBeInTheDocument();
    expect(screen.queryByText("Labels")).not.toBeInTheDocument();
    expect(screen.queryByText("Axis")).not.toBeInTheDocument();
  });
});

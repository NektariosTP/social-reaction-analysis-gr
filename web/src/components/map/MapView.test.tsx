import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
vi.mock("maplibre-gl");
import maplibregl from "maplibre-gl";
import type { GeoJsonFeature } from "../../client/types.gen";
import { MapView } from "./MapView";

vi.mock("../../api/queries", () => ({
  useEvent: () => ({
    data: {
      id: "evt-1",
      action_forms: [],
      thematic_fields: [],
      channel: null,
      intensity: null,
      summary_el: null,
      summary_en: "Preview headline",
      source_count: 2,
      articles: [],
    },
    isLoading: false,
    isError: false,
  }),
}));

const feature: GeoJsonFeature = {
  type: "Feature",
  geometry: { type: "Point", coordinates: [23.7, 38.0] },
  properties: {
    id: "evt-1",
    action_forms: [],
    thematic_fields: [],
    channel: null,
    intensity: null,
    summary_en: "Preview headline",
    article_count: 3,
    first_seen: null,
  },
};

describe("MapView", () => {
  it("initializes the map with a minZoom floor and the new default zoom", () => {
    render(<MapView features={[]} onSelectEvent={vi.fn()} />);
    const calls = (maplibregl as unknown as { mapConstructorCalls: Record<string, unknown>[] })
      .mapConstructorCalls;
    expect(calls.at(-1)).toEqual(expect.objectContaining({ zoom: 7.5, minZoom: 5.6 }));
  });

  it("renders the cluster popup when a selected feature and onClosePopup are provided", () => {
    render(
      <MapView features={[feature]} onSelectEvent={vi.fn()} selectedId="evt-1" onClosePopup={vi.fn()} />,
    );
    expect(screen.getByText("Preview headline")).toBeInTheDocument();
  });

  it("does not render the cluster popup when onClosePopup is not provided", () => {
    render(<MapView features={[feature]} onSelectEvent={vi.fn()} selectedId="evt-1" />);
    expect(screen.queryByText("Preview headline")).not.toBeInTheDocument();
  });
});

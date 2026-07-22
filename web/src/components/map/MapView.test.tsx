import { describe, expect, it, vi } from "vitest";
import { render } from "@testing-library/react";
vi.mock("maplibre-gl");
import maplibregl from "maplibre-gl";
import { MapView } from "./MapView";

describe("MapView", () => {
  it("initializes the map with a minZoom floor and the new default zoom", () => {
    render(<MapView features={[]} onSelectEvent={vi.fn()} />);
    const calls = (maplibregl as unknown as { mapConstructorCalls: Record<string, unknown>[] })
      .mapConstructorCalls;
    expect(calls.at(-1)).toEqual(expect.objectContaining({ zoom: 7.5, minZoom: 5.6 }));
  });
});

import { describe, expect, it, vi } from "vitest";
import { render } from "@testing-library/react";

// Mock maplibre-gl before importing MapView
vi.mock("maplibre-gl");
vi.mock("maplibre-gl/dist/maplibre-gl.css");

import maplibregl from "maplibre-gl";
import { MapView } from "./MapView";

describe("MapView", () => {
  it("initializes the map with a minZoom floor and the new default zoom", () => {
    render(<MapView features={[]} onSelectEvent={vi.fn()} />);
    const lastInstance = (maplibregl.Map as any).getLastInstance();
    expect(lastInstance?.opts).toEqual(expect.objectContaining({ zoom: 7.5, minZoom: 5.6 }));
  });
});

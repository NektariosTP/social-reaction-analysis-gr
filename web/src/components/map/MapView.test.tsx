import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
vi.mock("maplibre-gl");
import maplibregl from "maplibre-gl";
import type { GeoJsonFeature } from "../../client/types.gen";
import { MapView } from "./MapView";
import styles from "./MapView.module.css";

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
      article_count: 2,
      articles: [],
    },
    isLoading: false,
    isError: false,
  }),
}));

vi.mock("../../hooks/useIsMobile", () => ({ useIsMobile: vi.fn(() => false) }));
import { useIsMobile } from "../../hooks/useIsMobile";

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
    expect(calls.at(-1)).toEqual(expect.objectContaining({ zoom: 6.5, minZoom: 5.6 }));
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

  it("does not render the cluster popup when showPopup is false", () => {
    render(
      <MapView
        features={[feature]}
        onSelectEvent={vi.fn()}
        selectedId="evt-1"
        onClosePopup={vi.fn()}
        showPopup={false}
      />,
    );
    expect(screen.queryByText("Preview headline")).not.toBeInTheDocument();
  });

  it("uses a lower initial zoom on mobile, leaving desktop's zoom untouched", () => {
    (useIsMobile as unknown as ReturnType<typeof vi.fn>).mockReturnValueOnce(true);
    render(<MapView features={[]} onSelectEvent={vi.fn()} />);
    const calls = (maplibregl as unknown as { mapConstructorCalls: Record<string, unknown>[] })
      .mapConstructorCalls;
    expect(calls.at(-1)).toEqual(expect.objectContaining({ zoom: 5.6, minZoom: 5.6 }));
  });

  it("pads the map clear of the header and bottom sheet on mobile after load", () => {
    (useIsMobile as unknown as ReturnType<typeof vi.fn>).mockReturnValue(true);
    const setPadding = vi.fn();
    const mapProto = (maplibregl as unknown as { Map: { prototype: { setPadding: unknown } } }).Map
      .prototype;
    const original = mapProto.setPadding;
    mapProto.setPadding = setPadding;
    try {
      render(<MapView features={[]} onSelectEvent={vi.fn()} headerHeight={80} bottomInset={200} />);
      expect(setPadding).toHaveBeenCalledWith({ top: 96, bottom: 216, left: 0, right: 0 });
    } finally {
      mapProto.setPadding = original;
    }
  });
});

  it("constructs both event and cluster markers with an explicit center anchor", () => {
    render(
      <MapView features={[feature]} onSelectEvent={vi.fn()} selectedId={null} />,
    );
    const calls = (maplibregl as unknown as { markerConstructorCalls: Record<string, unknown>[] })
      .markerConstructorCalls;
    expect(calls.length).toBeGreaterThan(0);
    for (const call of calls) {
      expect(call.anchor).toBe("center");
    }
  });

  it("gives marker elements position:absolute so they don't fight maplibre's own placement", () => {
    render(
      <MapView features={[feature]} onSelectEvent={vi.fn()} selectedId={null} />,
    );
    const calls = (maplibregl as unknown as { markerConstructorCalls: Record<string, unknown>[] })
      .markerConstructorCalls;
    expect(calls.length).toBeGreaterThan(0);
    for (const call of calls) {
      const el = call.element as HTMLElement;
      expect(getComputedStyle(el).position).toBe("absolute");
    }
  });

  it("adds the multi-location overlay layers", () => {
    const mock = maplibregl as unknown as { mapLayerCalls: { layer: { id: string } }[] };
    mock.mapLayerCalls.length = 0;
    render(<MapView features={[feature]} onSelectEvent={vi.fn()} selectedId={null} />);
    const layerIds = mock.mapLayerCalls.map((l) => l.layer.id);
    expect(layerIds).toEqual(expect.arrayContaining(["event-connectors", "event-secondaries"]));
  });

it("renders clustered nearby events as an orbit constellation, not a plain count bubble", () => {
  const near: GeoJsonFeature = {
    ...feature,
    geometry: { type: "Point", coordinates: [23.701, 38.001] },
    properties: { ...feature.properties, id: "evt-2" },
  };
  const calls = (maplibregl as unknown as { markerConstructorCalls: Record<string, unknown>[] })
    .markerConstructorCalls;
  calls.length = 0;
  render(<MapView features={[feature, near]} onSelectEvent={vi.fn()} selectedId={null} />);
  // At the mock's default zoom (5.6) two adjacent points cluster into one marker.
  const hasOrbit = calls.some((c) =>
    (c.element as HTMLElement).querySelector('[data-role="orbiter"]'),
  );
  expect(hasOrbit).toBe(true);
});

it("still expands the cluster on click via easeTo", () => {
  const near: GeoJsonFeature = {
    ...feature,
    geometry: { type: "Point", coordinates: [23.701, 38.001] },
    properties: { ...feature.properties, id: "evt-2" },
  };
  const easeTo = vi.fn();
  const mapProto = (maplibregl as unknown as { Map: { prototype: { easeTo: unknown } } })
    .Map.prototype;
  const original = mapProto.easeTo;
  mapProto.easeTo = easeTo;
  try {
    const calls = (maplibregl as unknown as { markerConstructorCalls: Record<string, unknown>[] })
      .markerConstructorCalls;
    calls.length = 0;
    render(<MapView features={[feature, near]} onSelectEvent={vi.fn()} selectedId={null} />);
    const clusterCall = calls.find((c) =>
      (c.element as HTMLElement).querySelector('[data-role="orbiter"]'),
    );
    (clusterCall!.element as HTMLElement).dispatchEvent(new MouseEvent("click", { bubbles: true }));
    expect(easeTo).toHaveBeenCalled();
  } finally {
    mapProto.easeTo = original;
  }
});

it("plays the spring-in entrance only on a zoom-triggered render, not a plain pan", () => {
  const near: GeoJsonFeature = {
    ...feature,
    geometry: { type: "Point", coordinates: [23.701, 38.001] },
    properties: { ...feature.properties, id: "evt-2" },
  };
  const calls = (maplibregl as unknown as { markerConstructorCalls: Record<string, unknown>[] })
    .markerConstructorCalls;
  const mapInstances = (
    maplibregl as unknown as { mapInstances: { trigger: (event: string) => void }[] }
  ).mapInstances;
  render(<MapView features={[feature, near]} onSelectEvent={vi.fn()} selectedId={null} />);
  const map = mapInstances.at(-1)!;

  calls.length = 0;
  map.trigger("moveend");
  const pannedCluster = calls.find((c) =>
    (c.element as HTMLElement).querySelector('[data-role="orbiter"]'),
  )!.element as HTMLElement;
  expect(pannedCluster.querySelector<HTMLElement>('[data-role="orbiter"]')?.style.opacity).toBe("");

  calls.length = 0;
  map.trigger("zoomstart");
  map.trigger("zoomend");
  const zoomedCluster = calls.find((c) =>
    (c.element as HTMLElement).querySelector('[data-role="orbiter"]'),
  )!.element as HTMLElement;
  expect(zoomedCluster.querySelector<HTMLElement>('[data-role="orbiter"]')?.style.opacity).toBe("0");
});

/** Run `body` with the mock map reporting `zoom`, restoring the original after. */
function withZoom(zoom: number, body: () => void) {
  const mapProto = (maplibregl as unknown as { Map: { prototype: { getZoom: unknown } } }).Map
    .prototype;
  const original = mapProto.getZoom;
  mapProto.getZoom = () => zoom;
  try {
    body();
  } finally {
    mapProto.getZoom = original;
  }
}

it("shows no location subtitle below the zoom threshold, even for an un-clustered marker", () => {
  // Regression: subtitles used to appear as soon as an event was un-clustered
  // (i.e. at country/region overview) — far too early.
  const named: GeoJsonFeature = {
    ...feature,
    properties: {
      ...feature.properties,
      locations: [{ lat: 38.0, lon: 23.7, label: "Σύνταγμα", is_primary: true }],
    },
  };
  const calls = (maplibregl as unknown as { markerConstructorCalls: Record<string, unknown>[] })
    .markerConstructorCalls;
  calls.length = 0;
  // Mock's default getZoom() is 5.6 — well below LABEL_MIN_ZOOM (11).
  render(<MapView features={[named]} onSelectEvent={vi.fn()} selectedId={null} />);
  const anyLabel = calls.some((c) =>
    (c.element as HTMLElement).querySelector('[data-role="location-label"]'),
  );
  expect(anyLabel).toBe(false);
});

it("shows the primary location's admin-saved name once zoomed in past the threshold", () => {
  const named: GeoJsonFeature = {
    ...feature,
    properties: {
      ...feature.properties,
      locations: [{ lat: 38.0, lon: 23.7, label: "Σύνταγμα", is_primary: true }],
    },
  };
  const calls = (maplibregl as unknown as { markerConstructorCalls: Record<string, unknown>[] })
    .markerConstructorCalls;
  withZoom(12, () => {
    calls.length = 0;
    render(<MapView features={[named]} onSelectEvent={vi.fn()} selectedId={null} />);
    const label = calls
      .map((c) => (c.element as HTMLElement).querySelector('[data-role="location-label"]'))
      .find(Boolean);
    expect(label?.textContent).toBe("Σύνταγμα");
  });
});

it("adds a separate subtitle marker for each named secondary location when zoomed in", () => {
  const multi: GeoJsonFeature = {
    ...feature,
    properties: {
      ...feature.properties,
      locations: [
        { lat: 38.0, lon: 23.7, label: "Σύνταγμα", is_primary: true },
        { lat: 40.64, lon: 22.94, label: "Θεσσαλονίκη", is_primary: false },
      ],
    },
  };
  const calls = (maplibregl as unknown as { markerConstructorCalls: Record<string, unknown>[] })
    .markerConstructorCalls;
  withZoom(12, () => {
    calls.length = 0;
    render(<MapView features={[multi]} onSelectEvent={vi.fn()} selectedId={null} />);
    const secondaryLabelCall = calls.find(
      (c) => (c.element as HTMLElement).textContent === "Θεσσαλονίκη",
    );
    expect(secondaryLabelCall).toBeDefined();
    expect(secondaryLabelCall?.anchor).toBe("top");
  });
});

it("keeps a secondary's subtitle even when its event's primary is folded into a cluster", () => {
  // Regression: secondary subtitles used to be gated on the primary being an
  // un-clustered, in-view marker, so they vanished the moment the primary
  // joined a cluster or panned off screen.
  const multi: GeoJsonFeature = {
    ...feature,
    properties: {
      ...feature.properties,
      locations: [
        { lat: 38.0, lon: 23.7, label: "Σύνταγμα", is_primary: true },
        { lat: 40.64, lon: 22.94, label: "Θεσσαλονίκη", is_primary: false },
      ],
    },
  };
  // A second event right on top of `multi`'s primary, so at the test zoom the two
  // primaries cluster and `multi` is never rendered as its own marker.
  const near: GeoJsonFeature = {
    ...feature,
    geometry: { type: "Point", coordinates: [23.7001, 38.0001] },
    properties: { ...feature.properties, id: "evt-2" },
  };
  const calls = (maplibregl as unknown as { markerConstructorCalls: Record<string, unknown>[] })
    .markerConstructorCalls;
  withZoom(12, () => {
    calls.length = 0;
    render(<MapView features={[multi, near]} onSelectEvent={vi.fn()} selectedId={null} />);
    // Primaries clustered → no "Σύνταγμα" primary subtitle …
    const primaryLabel = calls.find(
      (c) => (c.element as HTMLElement).querySelector('[data-role="location-label"]')?.textContent ===
        "Σύνταγμα",
    );
    expect(primaryLabel).toBeUndefined();
    // … but the far-away secondary keeps its own subtitle.
    const secondaryLabelCall = calls.find(
      (c) => (c.element as HTMLElement).textContent === "Θεσσαλονίκη",
    );
    expect(secondaryLabelCall).toBeDefined();
  });
});

it("adds a zooming motion cue on zoomstart and removes it on zoomend", () => {
  const mapInstances = (
    maplibregl as unknown as { mapInstances: { trigger: (event: string) => void }[] }
  ).mapInstances;
  render(<MapView features={[feature]} onSelectEvent={vi.fn()} selectedId={null} />);
  const map = mapInstances.at(-1)!;
  const container = screen.getByTestId("map-canvas");

  expect(container.classList.contains(styles.clusterZooming)).toBe(false);
  map.trigger("zoomstart");
  expect(container.classList.contains(styles.clusterZooming)).toBe(true);
  map.trigger("zoomend");
  expect(container.classList.contains(styles.clusterZooming)).toBe(false);
});

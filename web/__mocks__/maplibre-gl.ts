export const markerConstructorCalls: Record<string, unknown>[] = [];

export class Marker {
  private el: HTMLElement;
  private lngLat: [number, number] = [0, 0];
  constructor(opts: { element: HTMLElement; anchor?: string }) {
    this.el = opts.element;
    markerConstructorCalls.push(opts);
  }
  setLngLat(lngLat: [number, number]) {
    this.lngLat = lngLat;
    return this;
  }
  addTo() {
    return this;
  }
  remove() {
    return this;
  }
  getElement() {
    return this.el;
  }
  getLngLat() {
    return this.lngLat;
  }
}

export class NavigationControl {}
export class FullscreenControl {}

export class LngLatBounds {
  private bounds: [number, number, number, number] | null = null;
  extend(coord: [number, number]) {
    this.bounds = this.bounds
      ? [
          Math.min(this.bounds[0], coord[0]),
          Math.min(this.bounds[1], coord[1]),
          Math.max(this.bounds[2], coord[0]),
          Math.max(this.bounds[3], coord[1]),
        ]
      : [coord[0], coord[1], coord[0], coord[1]];
    return this;
  }
}

export class Popup {
  private container: HTMLElement | null = null;
  private lngLat: [number, number] = [0, 0];
  constructor(private options: Record<string, unknown> = {}) {}
  setLngLat(lngLat: [number, number]) {
    this.lngLat = lngLat;
    return this;
  }
  getLngLat() {
    return this.lngLat;
  }
  setDOMContent(el: HTMLElement) {
    this.container = el;
    return this;
  }
  addTo() {
    if (this.container) document.body.appendChild(this.container);
    return this;
  }
  remove() {
    this.container?.remove();
    return this;
  }
  on() {
    return this;
  }
  off() {
    return this;
  }
}

type Handler = (...args: unknown[]) => void;

export const mapConstructorCalls: Record<string, unknown>[] = [];
export const mapSourceCalls: { id: string; source: Record<string, unknown> }[] = [];
export const mapLayerCalls: { layer: Record<string, unknown> }[] = [];
export const mapSetDataCalls: { id: string; data: unknown }[] = [];

export class Map {
  private handlers: Record<string, Handler[]> = {};
  private sources = new Set<string>();
  private layers = new Set<string>();
  constructor(public opts: Record<string, unknown>) {
    mapConstructorCalls.push(opts);
  }
  addControl() {
    return this;
  }
  isStyleLoaded() {
    return true;
  }
  once(event: string, cb: Handler) {
    if (event === "load") cb();
  }
  on(event: string, layerOrCb: string | Handler, cb?: Handler) {
    const handler = (typeof layerOrCb === "function" ? layerOrCb : cb) as Handler;
    (this.handlers[event] ??= []).push(handler);
  }
  off() {}
  setPaintProperty() {}
  getCanvas() {
    return { style: {} as CSSStyleDeclaration };
  }
  remove() {}
  getBounds() {
    return { toArray: () => [[-180, -85], [180, 85]] };
  }
  getZoom() {
    return 5.6;
  }
  easeTo() {}
  flyTo() {}
  addSource(id: string, source: Record<string, unknown>) {
    this.sources.add(id);
    mapSourceCalls.push({ id, source });
  }
  getSource(id: string) {
    return this.sources.has(id)
      ? { setData: (data: unknown) => mapSetDataCalls.push({ id, data }) }
      : undefined;
  }
  removeSource(id: string) {
    this.sources.delete(id);
  }
  addLayer(layer: Record<string, unknown>) {
    this.layers.add(layer.id as string);
    mapLayerCalls.push({ layer });
  }
  getLayer(id: string) {
    return this.layers.has(id) ? { id } : undefined;
  }
  removeLayer(id: string) {
    this.layers.delete(id);
  }
  setLayoutProperty() {}
  setFeatureState() {}
  removeFeatureState() {}
  fitBounds() {}
  queryRenderedFeatures() {
    return [];
  }
}

export default {
  Map,
  Marker,
  Popup,
  NavigationControl,
  FullscreenControl,
  LngLatBounds,
  mapConstructorCalls,
  markerConstructorCalls,
  mapSourceCalls,
  mapLayerCalls,
  mapSetDataCalls,
};

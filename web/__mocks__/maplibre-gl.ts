export class Marker {
  private el: HTMLElement;
  private lngLat: [number, number] = [0, 0];
  constructor(opts: { element: HTMLElement }) {
    this.el = opts.element;
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

type Handler = () => void;

export class Map {
  private handlers: Record<string, Handler[]> = {};
  constructor(_opts: unknown) {}
  addControl() {
    return this;
  }
  isStyleLoaded() {
    return true;
  }
  once(event: string, cb: Handler) {
    if (event === "load") cb();
  }
  on(event: string, cb: Handler) {
    (this.handlers[event] ??= []).push(cb);
  }
  off() {}
  remove() {}
  getBounds() {
    return { toArray: () => [[-180, -85], [180, 85]] };
  }
  getZoom() {
    return 5.6;
  }
  easeTo() {}
  flyTo() {}
}

export default { Map, Marker, NavigationControl, FullscreenControl };

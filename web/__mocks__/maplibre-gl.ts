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

type Handler = () => void;

export const mapConstructorCalls: Record<string, unknown>[] = [];

export class Map {
  private handlers: Record<string, Handler[]> = {};
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

export default { Map, Marker, Popup, NavigationControl, FullscreenControl, mapConstructorCalls };

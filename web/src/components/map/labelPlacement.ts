/**
 * Screen-space collision suppression for marker location labels.
 *
 * Labels are absolutely positioned directly below their bubbles, so nearby
 * markers' labels overlap into an unreadable pile. Rather than let them stack,
 * we place them greedily by priority (the selected marker first, so its label is
 * never suppressed) and drop any whose box would overlap one already placed.
 * Suppressed markers simply render without a subtitle — they stay clickable and
 * the location is still shown in the popup.
 */

export interface LabelBox {
  id: string;
  /** Horizontal centre of the label, in screen pixels. */
  x: number;
  /** Top edge of the label, in screen pixels. */
  y: number;
  width: number;
  height: number;
  /** Higher wins a collision; the selected marker gets the top value. */
  priority: number;
}

export interface ScreenPoint {
  x: number;
  y: number;
}

const LABEL_MAX_WIDTH = 170; // keep in sync with .locationLabel max-width
const LABEL_CHAR_PX = 6; // ~avg glyph advance at the 10px ui font
const LABEL_PADDING_X = 14; // horizontal padding + border
const LABEL_LINE_HEIGHT = 12; // 10px font * 1.2 line-height
const LABEL_PADDING_Y = 6; // vertical padding + border

/**
 * Approximate on-screen box for a label of `text` whose top edge sits `offsetY`
 * px below the marker anchor at `point`. Width/height are estimated from text
 * length and the 2-line clamp — exact glyph metrics aren't needed for collision
 * testing, only a close-enough footprint.
 */
export function estimateLabelBox(
  id: string,
  text: string,
  point: ScreenPoint,
  offsetY: number,
  priority: number,
): LabelBox {
  const singleLine = text.length * LABEL_CHAR_PX + LABEL_PADDING_X;
  const width = Math.min(singleLine, LABEL_MAX_WIDTH);
  const lines = singleLine > LABEL_MAX_WIDTH ? 2 : 1;
  const height = lines * LABEL_LINE_HEIGHT + LABEL_PADDING_Y;
  return { id, x: point.x, y: point.y + offsetY, width, height, priority };
}

interface Rect {
  left: number;
  right: number;
  top: number;
  bottom: number;
}

function toRect(b: LabelBox): Rect {
  return {
    left: b.x - b.width / 2,
    right: b.x + b.width / 2,
    top: b.y,
    bottom: b.y + b.height,
  };
}

function overlaps(a: Rect, b: Rect): boolean {
  return a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top;
}

/** Ids of the labels that should render, highest priority first, no two overlapping. */
export function selectVisibleLabels(boxes: LabelBox[]): Set<string> {
  const ordered = [...boxes].sort((a, b) => b.priority - a.priority);
  const placed: Rect[] = [];
  const visible = new Set<string>();
  for (const box of ordered) {
    const rect = toRect(box);
    if (placed.some((p) => overlaps(p, rect))) continue;
    placed.push(rect);
    visible.add(box.id);
  }
  return visible;
}

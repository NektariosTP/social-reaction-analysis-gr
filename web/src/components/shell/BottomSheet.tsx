import { useRef, useState } from "react";
import styles from "./BottomSheet.module.css";

interface BottomSheetProps {
  children: React.ReactNode;
  /** BottomNav's measured height (px) — the sheet's bottom edge sits here,
   * not at the true viewport edge, so it doesn't cover the nav bar. */
  bottomOffset: number;
}

/** Mobile-only draggable sheet: toggles between a peek and an expanded
 * height. Which content it shows is entirely owned by the parent (via
 * `children`, chosen by the active BottomNav tab) — this component only
 * handles sizing/dragging. */
export function BottomSheet({ children, bottomOffset }: BottomSheetProps) {
  const [expanded, setExpanded] = useState(false);
  const drag = useRef<{ startY: number; moved: boolean } | null>(null);
  // A real drag also fires a trailing click event on release; suppress that
  // one click so it doesn't immediately re-toggle what the drag just set.
  const suppressNextClick = useRef(false);

  function onHandlePointerDown(e: React.PointerEvent) {
    drag.current = { startY: e.clientY, moved: false };
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
  }
  function onHandlePointerMove(e: React.PointerEvent) {
    if (!drag.current) return;
    const dy = e.clientY - drag.current.startY;
    if (Math.abs(dy) > 8) {
      drag.current.moved = true;
      setExpanded(dy < 0); // drag up -> expand, drag down -> collapse
    }
  }
  function onHandlePointerUp() {
    if (drag.current?.moved) suppressNextClick.current = true;
    drag.current = null;
  }
  function onHandleClick() {
    if (suppressNextClick.current) {
      suppressNextClick.current = false;
      return;
    }
    setExpanded((v) => !v);
  }

  return (
    <div
      className={styles.sheet}
      data-testid="bottom-sheet"
      data-expanded={expanded ? "true" : "false"}
      style={{ bottom: bottomOffset }}
    >
      <button
        type="button"
        className={styles.handle}
        data-testid="sheet-handle"
        aria-label="Resize panel"
        onPointerDown={onHandlePointerDown}
        onPointerMove={onHandlePointerMove}
        onPointerUp={onHandlePointerUp}
        onClick={onHandleClick}
      >
        <span className={styles.grip} />
      </button>

      <div className={styles.body} data-testid="sheet-body">
        {children}
      </div>
    </div>
  );
}

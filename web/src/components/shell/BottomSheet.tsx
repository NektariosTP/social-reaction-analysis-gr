import { useEffect, useRef, useState } from "react";
import styles from "./BottomSheet.module.css";

interface BottomSheetProps {
  panels: React.ReactNode[];
  activePanel: number;
  onActivePanelChange: (index: number) => void;
  footer?: React.ReactNode;
}

/** Mobile-only bottom sheet: draggable between a peek and an expanded height,
 * with horizontally scroll-snapped full-width panels and page dots. The parent
 * mounts this only on mobile and owns the active-panel index. */
export function BottomSheet({ panels, activePanel, onActivePanelChange, footer }: BottomSheetProps) {
  const [expanded, setExpanded] = useState(false);
  const stripRef = useRef<HTMLDivElement>(null);
  const drag = useRef<{ startY: number; moved: boolean } | null>(null);
  // A real drag also fires a trailing click event on release; suppress that
  // one click so it doesn't immediately re-toggle what the drag just set.
  const suppressNextClick = useRef(false);

  // Scroll the strip to the controlled active panel when it changes externally
  // (e.g. a map tap selects an event in the Feed panel).
  useEffect(() => {
    const strip = stripRef.current;
    if (!strip) return;
    const target = activePanel * strip.clientWidth;
    if (Math.abs(strip.scrollLeft - target) > 1) {
      strip.scrollTo({ left: target, behavior: "smooth" });
    }
  }, [activePanel]);

  function handleScroll() {
    const strip = stripRef.current;
    if (!strip || strip.clientWidth === 0) return;
    const index = Math.round(strip.scrollLeft / strip.clientWidth);
    if (index !== activePanel) onActivePanelChange(index);
  }

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
    <div className={styles.sheet} data-testid="bottom-sheet" data-expanded={expanded ? "true" : "false"}>
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

      <div className={styles.strip} ref={stripRef} onScroll={handleScroll}>
        {panels.map((panel, i) => (
          <div className={styles.panel} data-testid="sheet-panel" key={i}>
            {panel}
          </div>
        ))}
      </div>

      {panels.length > 1 && (
        <div className={styles.dots}>
          {panels.map((_, i) => (
            <span
              key={i}
              className={styles.dot}
              data-testid="sheet-dot"
              data-active={i === activePanel ? "true" : undefined}
            />
          ))}
        </div>
      )}

      {footer && <div className={styles.footer}>{footer}</div>}
    </div>
  );
}

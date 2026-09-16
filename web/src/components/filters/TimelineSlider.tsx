import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import styles from "./TimelineSlider.module.css";

interface TimelineSliderProps {
  /** ISO YYYY-MM-DD local day, or null for the Live (present) view. */
  value: string | null;
  onChange: (day: string | null) => void;
  /** How many days back the leftmost stop reaches. Default 30. */
  maxDaysBack?: number;
}

/** Local-time YYYY-MM-DD for `n` days before today (n=0 → today). */
function isoNDaysAgo(n: number): string {
  const d = new Date();
  d.setHours(0, 0, 0, 0);
  d.setDate(d.getDate() - n);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

/** Whole days between an ISO local day and today (0 = today, positive = past). */
function daysBackForIso(iso: string): number {
  const [y, m, d] = iso.split("-").map(Number);
  const then = new Date(y, m - 1, d);
  then.setHours(0, 0, 0, 0);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((today.getTime() - then.getTime()) / 86_400_000);
}

/** Slider position → selected day. Rightmost (pos === max) is Live (null). */
function posToDay(pos: number, maxDaysBack: number): string | null {
  const daysAgo = maxDaysBack - pos;
  return daysAgo <= 0 ? null : isoNDaysAgo(daysAgo);
}

/** Selected day → slider position (clamped into range). */
function valueToPos(value: string | null, maxDaysBack: number): number {
  if (value === null) return maxDaysBack;
  const back = daysBackForIso(value);
  return Math.min(Math.max(maxDaysBack - back, 0), maxDaysBack);
}

export function TimelineSlider({ value, onChange, maxDaysBack = 30 }: TimelineSliderProps) {
  const { t, i18n } = useTranslation();
  const ref = useRef<HTMLInputElement>(null);
  const [pos, setPos] = useState(() => valueToPos(value, maxDaysBack));

  // Follow external changes (e.g. Clear filters → Live) without fighting the drag.
  useEffect(() => {
    setPos(valueToPos(value, maxDaysBack));
  }, [value, maxDaysBack]);

  // Commit only on release: the native `change` event fires on mouseup/keyup,
  // not on every drag tick (which React's onChange would). One query per drag.
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const commit = () => onChange(posToDay(Number(el.value), maxDaysBack));
    el.addEventListener("change", commit);
    return () => el.removeEventListener("change", commit);
  }, [onChange, maxDaysBack]);

  const day = posToDay(pos, maxDaysBack);
  const label =
    day === null
      ? t("time.live")
      : new Intl.DateTimeFormat(i18n.language, {
          day: "numeric",
          month: "short",
          year: "numeric",
        }).format(new Date(Number(day.slice(0, 4)), Number(day.slice(5, 7)) - 1, Number(day.slice(8, 10))));

  return (
    <div className={styles.slider}>
      <input
        ref={ref}
        type="range"
        min={0}
        max={maxDaysBack}
        step={1}
        value={pos}
        onInput={(e) => setPos(Number((e.target as HTMLInputElement).value))}
        className={styles.range}
        aria-label={t("time.travelLabel")}
      />
      <span className={styles.label}>{label}</span>
    </div>
  );
}

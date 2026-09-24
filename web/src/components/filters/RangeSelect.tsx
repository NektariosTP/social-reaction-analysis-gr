import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { formatAbsoluteDate } from "../../utils/time";
import { useLang } from "../../hooks/useLang";
import styles from "./RangeSelect.module.css";

interface RangeSelectProps {
  windowDays: number | null;
  day: string | null;
  onChange: (next: { windowDays: number | null; day: string | null }) => void;
}

const PRESETS = [7, 15, 30] as const;

export function RangeSelect({ windowDays, day, onChange }: RangeSelectProps) {
  const { t } = useTranslation();
  const [lang] = useLang();
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    function onPointerDown(e: PointerEvent) {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setOpen(false);
    }
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  const presetLabel = (n: number) =>
    n === 7 ? t("range.last7") : n === 15 ? t("range.last15") : t("range.last30");

  const triggerLabel = day
    ? formatAbsoluteDate(day, lang)
    : windowDays
      ? presetLabel(windowDays)
      : t("range.live");

  function choosePreset(n: number | null) {
    onChange({ windowDays: n, day: null });
    setOpen(false);
  }

  return (
    <div className={styles.root} ref={rootRef}>
      <button
        type="button"
        className={styles.trigger}
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        {triggerLabel} {open ? "▴" : "▾"}
      </button>
      {open && (
        <div className={styles.menu}>
          <button
            type="button"
            className={styles.option}
            data-active={(windowDays === null && !day) || undefined}
            onClick={() => choosePreset(null)}
          >
            {t("range.live")}
            <span className={styles.sub}>{t("range.liveSubtitle")}</span>
          </button>
          {PRESETS.map((n) => (
            <button
              key={n}
              type="button"
              className={styles.option}
              data-active={windowDays === n || undefined}
              onClick={() => choosePreset(n)}
            >
              {presetLabel(n)}
            </button>
          ))}
          <label className={styles.dateRow}>
            <span>{t("range.exactDate")}</span>
            <input
              type="date"
              value={day ?? ""}
              onChange={(e) => onChange({ windowDays: null, day: e.target.value || null })}
            />
          </label>
        </div>
      )}
    </div>
  );
}

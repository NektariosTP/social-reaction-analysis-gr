import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import type { FilterState } from "../../hooks/useFilterState";
import { FilterPanel, RangePanel, RangeSelect } from "../filters";
import { BrandMark } from "../common";
import styles from "./HeaderBlock.module.css";

interface HeaderBlockProps {
  filters: FilterState;
  onToggleFilterValue: (key: "actionForms" | "thematicFields", value: string) => void;
  onSetFilters: (next: Partial<FilterState>) => void;
  trailing?: React.ReactNode;
}

type Panel = "range" | "filters" | null;

export function HeaderBlock({
  filters,
  onToggleFilterValue,
  onSetFilters,
  trailing,
}: HeaderBlockProps) {
  const { t } = useTranslation();
  const [activePanel, setActivePanel] = useState<Panel>(null);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!activePanel) return;

    function handlePointerDown(e: PointerEvent) {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) {
        setActivePanel(null);
      }
    }
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") setActivePanel(null);
    }

    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [activePanel]);

  function togglePanel(panel: Exclude<Panel, null>) {
    setActivePanel((current) => (current === panel ? null : panel));
  }

  return (
    <div ref={rootRef}>
      <div className={styles.brandRow}>
        <BrandMark size={24} className={styles.mark} />
        <span className={styles.brandName}>{t("brand")}</span>
        {trailing && <div className={styles.trailing}>{trailing}</div>}
      </div>
      <div className={styles.searchRow}>
        <RangeSelect
          windowDays={filters.windowDays}
          day={filters.day}
          open={activePanel === "range"}
          onClick={() => togglePanel("range")}
        />
        <button
          type="button"
          className={styles.pillTrigger}
          aria-expanded={activePanel === "filters"}
          onClick={() => togglePanel("filters")}
        >
          <span className={styles.pillIcon}>⚙️</span>
          <span className={styles.pillLabel}>{t("filters.title")}</span>
          <span className={styles.pillArrow}>{activePanel === "filters" ? "▴" : "▾"}</span>
        </button>
      </div>

      {activePanel === "range" && (
        <div className={styles.expansion}>
          <RangePanel windowDays={filters.windowDays} day={filters.day} onChange={onSetFilters} />
          <div className={styles.expansionActions}>
            <button type="button" className={styles.doneBtn} onClick={() => setActivePanel(null)}>
              {t("filters.done")}
            </button>
          </div>
        </div>
      )}

      {activePanel === "filters" && (
        <div className={styles.expansion}>
          <FilterPanel filters={filters} onToggle={onToggleFilterValue} onSetFilters={onSetFilters} />
          <div className={styles.expansionActions}>
            <button
              type="button"
              className={styles.clearBtn}
              onClick={() =>
                onSetFilters({
                  actionForms: [],
                  thematicFields: [],
                  channel: null,
                  intensity: null,
                  day: null,
                  windowDays: null,
                })
              }
            >
              {t("filters.clear")}
            </button>
            <button type="button" className={styles.doneBtn} onClick={() => setActivePanel(null)}>
              {t("filters.done")}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

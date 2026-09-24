import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import type { FilterState } from "../../hooks/useFilterState";
import { FilterPanel, RangeSelect } from "../filters";
import { BrandMark } from "../common";
import styles from "./HeaderBlock.module.css";

interface HeaderBlockProps {
  filters: FilterState;
  onToggleFilterValue: (key: "actionForms" | "thematicFields", value: string) => void;
  onSetFilters: (next: Partial<FilterState>) => void;
  trailing?: React.ReactNode;
}

export function HeaderBlock({
  filters,
  onToggleFilterValue,
  onSetFilters,
  trailing,
}: HeaderBlockProps) {
  const { t } = useTranslation();
  const [filterOpen, setFilterOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!filterOpen) return;

    function handlePointerDown(e: PointerEvent) {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) {
        setFilterOpen(false);
      }
    }
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") setFilterOpen(false);
    }

    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [filterOpen]);

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
          onChange={onSetFilters}
        />
        <button
          className={styles.filterToggle}
          onClick={() => setFilterOpen((v) => !v)}
        >
          {filterOpen ? "⋀" : "⋁"} {t("filters.title")}
        </button>
      </div>

      {filterOpen && (
        <div className={styles.expansion}>
          <FilterPanel filters={filters} onToggle={onToggleFilterValue} onSetFilters={onSetFilters} />
          <div className={styles.expansionActions}>
            <button
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
            <button className={styles.doneBtn} onClick={() => setFilterOpen(false)}>
              {t("filters.done")}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

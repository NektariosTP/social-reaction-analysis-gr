import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import type { FilterState } from "../../hooks/useFilterState";
import { FilterPanel } from "../filters";
import { BrandMark } from "../common";
import styles from "./HeaderBlock.module.css";

type Expanded = "none" | "search" | "filter";

interface HeaderBlockProps {
  searchQuery: string;
  onSearchChange: (value: string) => void;
  filters: FilterState;
  onToggleFilterValue: (key: "actionForms" | "thematicFields", value: string) => void;
  onSetFilters: (next: Partial<FilterState>) => void;
  trailing?: React.ReactNode;
}

export function HeaderBlock({
  searchQuery,
  onSearchChange,
  filters,
  onToggleFilterValue,
  onSetFilters,
  trailing,
}: HeaderBlockProps) {
  const { t } = useTranslation();
  const [expanded, setExpanded] = useState<Expanded>("none");
  const rootRef = useRef<HTMLDivElement>(null);

  function closeSearch() {
    setExpanded("none");
  }

  useEffect(() => {
    if (expanded === "none") return;

    function handlePointerDown(e: PointerEvent) {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) {
        closeSearch();
      }
    }
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        closeSearch();
      }
    }

    document.addEventListener("pointerdown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("pointerdown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [expanded]);

  return (
    <div ref={rootRef}>
      <div className={styles.brandRow}>
        <BrandMark size={24} className={styles.mark} />
        <span className={styles.brandName}>{t("brand")}</span>
        {trailing && <div className={styles.trailing}>{trailing}</div>}
      </div>
      <div className={styles.searchRow}>
        <input
          className={styles.searchInput}
          placeholder={t("search.placeholder")}
          value={searchQuery}
          onFocus={() => setExpanded("search")}
          onChange={(e) => onSearchChange(e.target.value)}
        />
        <button
          className={styles.filterToggle}
          onClick={() => setExpanded((e) => (e === "filter" ? "none" : "filter"))}
        >
          {expanded === "filter" ? "⋀" : "⋁"} {t("filters.title")}
        </button>
      </div>

      {expanded === "filter" && (
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
                  intensities: [],
                  timeRange: "all",
                })
              }
            >
              {t("filters.clear")}
            </button>
            <button className={styles.doneBtn} onClick={() => setExpanded("none")}>
              {t("filters.done")}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useLang } from "../../hooks/useLang";
import { useRecentSearches } from "../../hooks/useRecentSearches";
import type { FilterState } from "../../hooks/useFilterState";
import { REGIONS, type Region } from "../../i18n/regions";
import { FilterPanel } from "../filters";
import styles from "./HeaderBlock.module.css";

type Expanded = "none" | "search" | "filter";

interface HeaderBlockProps {
  searchQuery: string;
  onSearchChange: (value: string) => void;
  onSelectRegion: (region: Region) => void;
  filters: FilterState;
  onToggleFilterValue: (key: "actionForms" | "thematicFields" | "intensities", value: string) => void;
  onSetFilters: (next: Partial<FilterState>) => void;
}

export function HeaderBlock({
  searchQuery,
  onSearchChange,
  onSelectRegion,
  filters,
  onToggleFilterValue,
  onSetFilters,
}: HeaderBlockProps) {
  const { t } = useTranslation();
  const [lang] = useLang();
  const [expanded, setExpanded] = useState<Expanded>("none");
  const { recent, addRecent } = useRecentSearches();

  return (
    <div className={styles.block}>
      <div className={styles.brandRow}>
        <span className={styles.mark}>R</span>
        <span className={styles.brandName}>{t("brand")}</span>
        <span className={styles.live}>● {t("live")}</span>
      </div>
      <div className={styles.searchRow}>
        <input
          className={styles.searchInput}
          placeholder={t("search.placeholder")}
          value={searchQuery}
          onFocus={() => setExpanded("search")}
          onChange={(e) => onSearchChange(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") addRecent(searchQuery);
          }}
        />
        <button
          className={styles.filterToggle}
          onClick={() => setExpanded((e) => (e === "filter" ? "none" : "filter"))}
        >
          {expanded === "filter" ? "⋀" : "⋁"} {t("filters.title")}
        </button>
      </div>

      {expanded === "search" && (
        <div className={styles.expansion}>
          {recent.length > 0 && (
            <>
              <div className={styles.expansionLabel}>{t("search.recent")}</div>
              <div className={styles.chipRow}>
                {recent.map((term) => (
                  <button
                    key={term}
                    className={styles.shortcutChip}
                    onClick={() => {
                      onSearchChange(term);
                      setExpanded("none");
                    }}
                  >
                    {term}
                  </button>
                ))}
              </div>
            </>
          )}
          <div className={styles.expansionLabel}>{t("search.browseByRegion")}</div>
          <div className={styles.chipRow}>
            {REGIONS.map((region) => (
              <button
                key={region.en}
                className={styles.shortcutChip}
                onClick={() => {
                  onSelectRegion(region);
                  setExpanded("none");
                }}
              >
                {lang === "el" ? region.el : region.en}
              </button>
            ))}
          </div>
        </div>
      )}

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

import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useLang } from "../../hooks/useLang";
import type { FilterState } from "../../hooks/useFilterState";
import { REGIONS, type Region } from "../../i18n/regions";
import { FilterPanel } from "../filters";
import styles from "./HeaderBlock.module.css";

type Expanded = "none" | "search" | "filter";
type SearchView = "options" | "region";

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
  const [searchView, setSearchView] = useState<SearchView>("options");

  function closeSearch() {
    setExpanded("none");
    setSearchView("options");
  }

  return (
    <div>
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
          onFocus={() => {
            setExpanded("search");
            setSearchView("options");
          }}
          onChange={(e) => onSearchChange(e.target.value)}
        />
        <button
          className={styles.filterToggle}
          onClick={() => setExpanded((e) => (e === "filter" ? "none" : "filter"))}
        >
          {expanded === "filter" ? "⋀" : "⋁"} {t("filters.title")}
        </button>
      </div>

      {expanded === "search" && searchView === "options" && (
        <div className={styles.expansion}>
          <button className={styles.optionRow} onClick={() => setSearchView("region")}>
            <span>{t("search.browseByRegion")}</span>
            <span aria-hidden="true">›</span>
          </button>
        </div>
      )}

      {expanded === "search" && searchView === "region" && (
        <div className={styles.expansion}>
          <button className={styles.backRow} onClick={() => setSearchView("options")}>
            {t("search.back")}
          </button>
          <div className={styles.chipRow}>
            {REGIONS.map((region) => (
              <button
                key={region.en}
                className={styles.shortcutChip}
                onClick={() => {
                  onSelectRegion(region);
                  closeSearch();
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

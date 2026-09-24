import { useTranslation } from "react-i18next";
import type { FilterState } from "../../hooks/useFilterState";
import { LegendContent } from "../map/LegendContent";
import styles from "./LegendPanel.module.css";

interface LegendPanelProps {
  filters?: FilterState;
  onToggleFilterValue?: (key: "actionForms" | "thematicFields", value: string) => void;
  onSetFilters?: (next: Partial<FilterState>) => void;
}

/** Mobile "Legend" bottom-nav tab body — the shared axis reference content,
 * interactive as a filter surface when filter props are supplied. */
export function LegendPanel({ filters, onToggleFilterValue, onSetFilters }: LegendPanelProps = {}) {
  const { t } = useTranslation();
  return (
    <div className={styles.panel}>
      <div className={styles.heading}>{t("legend.title")}</div>
      <LegendContent filters={filters} onToggleFilterValue={onToggleFilterValue} onSetFilters={onSetFilters} />
    </div>
  );
}

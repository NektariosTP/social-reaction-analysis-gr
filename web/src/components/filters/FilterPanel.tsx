import { useTranslation } from "react-i18next";
import { ACTION_FORM, THEMATIC_FIELD } from "../../i18n/taxonomy";
import type { FilterState } from "../../hooks/useFilterState";
import { AxisMultiSelect } from "./AxisMultiSelect";
import { ChannelSelect } from "./ChannelSelect";
import { IntensityRangeSelect } from "./IntensityRangeSelect";
import styles from "./FilterPanel.module.css";

const ACTION_FORM_OPTIONS = Object.keys(ACTION_FORM);
const THEMATIC_FIELD_OPTIONS = Object.keys(THEMATIC_FIELD);

interface FilterPanelProps {
  filters: FilterState;
  onToggle: (key: "actionForms" | "thematicFields", value: string) => void;
  onSetFilters: (next: Partial<FilterState>) => void;
}

export function FilterPanel({ filters, onToggle, onSetFilters }: FilterPanelProps) {
  const { t } = useTranslation();

  return (
    <div className={styles.panel}>
      <div className={styles.col}>
        <AxisMultiSelect
          title={t("filters.axis1")}
          options={ACTION_FORM_OPTIONS}
          selected={filters.actionForms}
          onToggle={(v) => onToggle("actionForms", v)}
          onClear={() => onSetFilters({ actionForms: [] })}
        />
        <ChannelSelect
          selected={filters.channel}
          onChange={(channel) => onSetFilters({ channel })}
        />
      </div>
      <div className={styles.col}>
        <AxisMultiSelect
          title={t("filters.axis2")}
          options={THEMATIC_FIELD_OPTIONS}
          selected={filters.thematicFields}
          onToggle={(v) => onToggle("thematicFields", v)}
          onClear={() => onSetFilters({ thematicFields: [] })}
        />
        <IntensityRangeSelect selected={filters.intensities} onSetFilters={onSetFilters} />
      </div>
    </div>
  );
}

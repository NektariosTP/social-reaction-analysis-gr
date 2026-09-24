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

  // DOM order Action, Theme, Channel, Intensity: a 2-col row-major grid places
  // Action/Theme on the top row and Channel/Intensity below (desktop, unchanged);
  // the single-col mobile grid stacks them Action → Theme → Channel → Intensity.
  return (
    <div className={styles.panel}>
      <AxisMultiSelect
        title={t("filters.axis1")}
        options={ACTION_FORM_OPTIONS}
        selected={filters.actionForms}
        onToggle={(v) => onToggle("actionForms", v)}
        onClear={() => onSetFilters({ actionForms: [] })}
      />
      <AxisMultiSelect
        title={t("filters.axis2")}
        options={THEMATIC_FIELD_OPTIONS}
        selected={filters.thematicFields}
        onToggle={(v) => onToggle("thematicFields", v)}
        onClear={() => onSetFilters({ thematicFields: [] })}
      />
      <ChannelSelect selected={filters.channel} onChange={(channel) => onSetFilters({ channel })} />
      <IntensityRangeSelect
        selected={filters.intensity}
        onChange={(intensity) => onSetFilters({ intensity })}
      />
    </div>
  );
}

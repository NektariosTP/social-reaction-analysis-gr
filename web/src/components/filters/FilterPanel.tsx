import { useTranslation } from "react-i18next";
import { ACTION_FORM, THEMATIC_FIELD } from "../../i18n/taxonomy";
import type { FilterState, TimeRange } from "../../hooks/useFilterState";
import { AxisMultiSelect } from "./AxisMultiSelect";
import { ChannelSelect } from "./ChannelSelect";
import { IntensityRangeSelect } from "./IntensityRangeSelect";
import { TimeRangeTabs } from "./TimeRangeTabs";
import styles from "./FilterPanel.module.css";

const ACTION_FORM_OPTIONS = Object.keys(ACTION_FORM);
const THEMATIC_FIELD_OPTIONS = Object.keys(THEMATIC_FIELD);

interface FilterPanelProps {
  filters: FilterState;
  onToggle: (key: "actionForms" | "thematicFields" | "intensities", value: string) => void;
  onSetFilters: (next: Partial<FilterState>) => void;
}

export function FilterPanel({ filters, onToggle, onSetFilters }: FilterPanelProps) {
  const { t } = useTranslation();

  return (
    <div className={styles.panel}>
      <div className={styles.timeRow}>
        <div style={{ fontSize: 9, fontWeight: 700, letterSpacing: "0.1em", textTransform: "uppercase", color: "var(--color-text-muted)", marginBottom: 6 }}>
          {t("filters.time")}
        </div>
        <TimeRangeTabs
          value={filters.timeRange}
          onChange={(timeRange: TimeRange) => onSetFilters({ timeRange })}
        />
      </div>

      <div className={styles.col}>
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
      </div>
      <div className={styles.col}>
        <ChannelSelect
          selected={filters.channel}
          onChange={(channel) => onSetFilters({ channel })}
        />
        <IntensityRangeSelect
          selected={filters.intensities}
          onToggle={(v) => onToggle("intensities", v)}
        />
      </div>
    </div>
  );
}

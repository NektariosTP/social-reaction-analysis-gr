import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { ACTION_FORM, THEMATIC_FIELD, CHANNEL, INTENSITY } from "../../i18n/taxonomy";
import { AxisValueChip, type ChipAxis } from "../common/AxisValueChip";
import styles from "./OnboardingOverlay.module.css";

const AXES: { titleKey: string; axis: ChipAxis; values: string[] }[] = [
  { titleKey: "filters.axis1", axis: "action", values: Object.keys(ACTION_FORM) },
  { titleKey: "filters.axis2", axis: "theme", values: Object.keys(THEMATIC_FIELD) },
  { titleKey: "filters.axis3", axis: "channel", values: Object.keys(CHANNEL) },
  { titleKey: "filters.axis4", axis: "intensity", values: Object.keys(INTENSITY) },
];

export function OnboardingOverlay({ onDismiss }: { onDismiss: () => void }) {
  const { t } = useTranslation();
  const navigate = useNavigate();

  return (
    <div className={styles.scrim} role="dialog" aria-modal="true">
      <div className={styles.modal}>
        <div className={styles.brandRow}>
          <span className={styles.mark}>R</span>
          <div>
            <div className={styles.brandName}>{t("brand")}</div>
            <div className={styles.subtitle}>{t("onboarding.subtitle")}</div>
          </div>
        </div>

        <h2 className={styles.title}>{t("onboarding.title")}</h2>
        <p className={styles.body}>{t("onboarding.body")}</p>

        <div className={styles.axesBox}>
          <div className={styles.axesTitle}>{t("onboarding.axesTitle")}</div>
          <div className={styles.axesGrid}>
            {AXES.map(({ titleKey, axis, values }) => (
              <div key={titleKey}>
                <div className={styles.axisLabel}>{t(titleKey)}</div>
                <div className={styles.chipRow} data-testid={`axis-${axis}-values`}>
                  {values.map((v) => (
                    <AxisValueChip key={v} axis={axis} value={v} />
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className={styles.ctaRow}>
          <button className={styles.primaryBtn} onClick={onDismiss}>
            {t("onboarding.start")}
          </button>
          <button
            className={styles.secondaryBtn}
            onClick={() => {
              onDismiss();
              navigate("/about");
            }}
          >
            {t("onboarding.methodology")}
          </button>
        </div>
        <div className={styles.skip} onClick={onDismiss}>
          {t("onboarding.skip")}
        </div>
      </div>
    </div>
  );
}

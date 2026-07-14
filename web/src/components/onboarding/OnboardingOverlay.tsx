import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useLang } from "../../hooks/useLang";
import { axisLabel } from "../../i18n";
import { ACTION_FORM, THEMATIC_FIELD, CHANNEL, INTENSITY } from "../../i18n/taxonomy";
import styles from "./OnboardingOverlay.module.css";

const AXES = [
  { titleKey: "filters.axis1", dict: ACTION_FORM },
  { titleKey: "filters.axis2", dict: THEMATIC_FIELD },
  { titleKey: "filters.axis3", dict: CHANNEL },
  { titleKey: "filters.axis4", dict: INTENSITY },
] as const;

export function OnboardingOverlay({ onDismiss }: { onDismiss: () => void }) {
  const { t } = useTranslation();
  const [lang] = useLang();
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
            {AXES.map(({ titleKey, dict }) => (
              <div key={titleKey}>
                <div className={styles.axisLabel}>{t(titleKey)}</div>
                <div className={styles.axisValues}>
                  {Object.keys(dict).map((v) => axisLabel(v, lang)).join(" · ")}
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

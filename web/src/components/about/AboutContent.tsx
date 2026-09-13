import { useTranslation } from "react-i18next";
import { AxisValueChip } from "../common/AxisValueChip";
import { AxisReferenceBlock } from "../common";
import { ACTION_FORM, THEMATIC_FIELD, CHANNEL, INTENSITY } from "../../i18n/taxonomy";
import styles from "./AboutContent.module.css";

/** The About content, rendered inside the About modal. */
export function AboutContent() {
  const { t } = useTranslation();

  return (
    <div>
      <div className={styles.header}>
        <h1 className={styles.title}>{t("about.title")}</h1>
        <p className={styles.lead}>{t("about.lead")}</p>
      </div>

      <div className={styles.grid3}>
        <div className={styles.col}>
          <div className={styles.colLabel}>{t("about.projectLabel")}</div>
          <p className={styles.p}>{t("about.projectP1")}</p>
          <p className={styles.p}>{t("about.projectP2")}</p>
          <div className={styles.citation}>
            <div style={{ opacity: 0.55, fontSize: 8, marginBottom: 4 }}>{t("about.citationLabel")}</div>
            <div>
              {t("about.citationAuthor")} <i>{t("about.citationTitle")}</i> {t("about.citationDetails")}
            </div>
          </div>
        </div>

        <div className={`${styles.col} ${styles.classCol}`}>
          <div className={styles.colLabel}>{t("about.classificationLabel")}</div>
          <AxisReferenceBlock label={`${t("filters.axis1")}`} color="var(--color-axis1)">
            <div className={styles.chipRow}>
              {Object.keys(ACTION_FORM).map((v) => (
                <AxisValueChip key={v} axis="action" value={v} />
              ))}
            </div>
          </AxisReferenceBlock>
          <AxisReferenceBlock label={`${t("filters.axis2")}`} color="var(--color-axis2)">
            <div className={styles.chipRow}>
              {Object.keys(THEMATIC_FIELD).map((v) => (
                <AxisValueChip key={v} axis="theme" value={v} />
              ))}
            </div>
          </AxisReferenceBlock>
          <AxisReferenceBlock label={`${t("filters.axis3")}`} color="var(--color-axis3)">
            <div className={styles.chipRow}>
              {Object.keys(CHANNEL).map((v) => (
                <AxisValueChip key={v} axis="channel" value={v} />
              ))}
            </div>
          </AxisReferenceBlock>
          <AxisReferenceBlock label={`${t("filters.axis4")}`}>
            <div className={styles.chipRow}>
              {Object.keys(INTENSITY).map((v) => (
                <AxisValueChip key={v} axis="intensity" value={v} />
              ))}
            </div>
            <div className={styles.axisNote}>{t("about.axisNote")}</div>
          </AxisReferenceBlock>
        </div>

        <div className={styles.col}>
          <div className={styles.colLabel}>{t("about.contactLabel")}</div>
          <a
            className={styles.linkRow}
            href="https://github.com/NektariosTP/social-reaction-analysis-gr"
            target="_blank"
            rel="noreferrer"
          >
            <span>{t("about.github")}</span>
            <span style={{ opacity: 0.5 }}>↗</span>
          </a>
          <a className={styles.linkRow} href="mailto:nektarios.tp@gmail.com">
            <span>{t("about.contact")}</span>
            <span style={{ opacity: 0.5 }}>↗</span>
          </a>
          <div className={styles.linkRow}>
            <span>{t("about.thesisPdf")}</span>
            <span style={{ opacity: 0.5 }}>{t("about.thesisRepo")}</span>
          </div>
          <p style={{ fontSize: 10, color: "var(--color-text-muted)", marginTop: 12 }}>
            {t("about.licenseUse")}
            <br />{t("about.licenseCopyright")}
          </p>
        </div>
      </div>
    </div>
  );
}

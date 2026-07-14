import { useTranslation } from "react-i18next";
import styles from "./ComingSoonBlock.module.css";

interface ComingSoonBlockProps {
  title: string;
  description: string;
}

/**
 * Placeholder for wireframe blocks with no backing API field yet (politician
 * quotes, trending hashtags, petitions, cluster timeline, related clusters,
 * NER spans, multi-location chips). Never fabricates content — states plainly
 * what will render here once the backend supports it.
 */
export function ComingSoonBlock({ title, description }: ComingSoonBlockProps) {
  const { t } = useTranslation();
  return (
    <div className={styles.block}>
      <span className={styles.badge}>{t("comingSoon")}</span>
      <div className={styles.title}>{title}</div>
      <div className={styles.description}>{description}</div>
    </div>
  );
}

import { useTranslation } from "react-i18next";
import styles from "./StatusMessage.module.css";

export function EmptyState({ message }: { message?: string }) {
  const { t } = useTranslation();
  return <div className={styles.wrap}>{message ?? t("empty.noEvents")}</div>;
}

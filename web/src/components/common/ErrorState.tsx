import { useTranslation } from "react-i18next";
import styles from "./StatusMessage.module.css";

export function ErrorState({ message }: { message?: string }) {
  const { t } = useTranslation();
  return <div className={`${styles.wrap} ${styles.error}`}>{message ?? t("error.generic")}</div>;
}

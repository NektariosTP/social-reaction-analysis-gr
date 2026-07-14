import { useTranslation } from "react-i18next";
import { useLang } from "../../hooks/useLang";
import { formatRelativeTime } from "../../utils/time";
import { ComingSoonBlock } from "../common";
import type { PoliticianQuoteData } from "./types";
import styles from "./PoliticianQuote.module.css";

export function PoliticianQuote({ data }: { data?: PoliticianQuoteData }) {
  const { t } = useTranslation();
  const [lang] = useLang();

  if (!data) {
    return (
      <ComingSoonBlock
        title={t("cluster.officialStatements")}
        description="Will surface politician/official social-media posts that NER links to this cluster, once source ingestion tracks named-actor statements."
      />
    );
  }

  return (
    <div className={styles.quote}>
      <span className={styles.avatar}>{data.handle.charAt(0).toUpperCase()}</span>
      <div>
        <div className={styles.meta}>
          {data.handle} · {data.platform} · {formatRelativeTime(data.timestampIso, lang)}
        </div>
        <div className={styles.text}>&ldquo;{data.quote}&rdquo;</div>
      </div>
    </div>
  );
}

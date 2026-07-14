import { useTranslation } from "react-i18next";
import { ComingSoonBlock } from "../common";

export function OfficialStatements() {
  const { t } = useTranslation();
  return (
    <ComingSoonBlock
      title={t("cluster.officialStatements")}
      description="Will list politician/official statements NER-linked to this cluster, once source ingestion tracks named-actor social posts."
    />
  );
}

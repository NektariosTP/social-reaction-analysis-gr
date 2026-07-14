import { useTranslation } from "react-i18next";
import { ComingSoonBlock } from "../common";

export function RelatedClusters() {
  const { t } = useTranslation();
  return (
    <ComingSoonBlock
      title={t("cluster.relatedClusters")}
      description="Will surface similar/nearby clusters (shared location or theme), once a cross-event similarity endpoint exists."
    />
  );
}

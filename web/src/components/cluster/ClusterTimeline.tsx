import { useTranslation } from "react-i18next";
import { ComingSoonBlock } from "../common";

export function ClusterTimeline() {
  const { t } = useTranslation();
  return (
    <ComingSoonBlock
      title={t("cluster.timeline")}
      description="Will show how the classification evolved as new sources arrived (e.g. an intensity upgrade timestamped mid-cluster), once the pipeline records a per-event audit trail."
    />
  );
}

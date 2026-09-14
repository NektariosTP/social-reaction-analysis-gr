import { useTranslation } from "react-i18next";
import type { ReactionSummary } from "../../client/types.gen";
import { dedupeUnions } from "../../utils/unionDedup";

function UnionRow({ reaction }: { reaction: ReactionSummary }) {
  return (
    <a
      href={reaction.url ?? undefined}
      target="_blank"
      rel="noreferrer"
      style={{
        display: "block",
        border: "1px solid var(--color-border)",
        borderRadius: "var(--radius-sm)",
        padding: "8px 11px",
        marginBottom: 6,
        textDecoration: "none",
        color: "inherit",
        fontSize: 11,
        fontWeight: 700,
      }}
    >
      {reaction.actor_name}
    </a>
  );
}

export function UnionSourceList({ reactions }: { reactions: ReactionSummary[] }) {
  const { t } = useTranslation();
  if (reactions.length === 0) return null;
  const [announcer, ...supporters] = dedupeUnions(reactions);

  return (
    <div>
      <div style={{ fontSize: 10, opacity: 0.6, marginBottom: 4 }}>
        📣 {t("cluster.announcedBy")}
      </div>
      <UnionRow reaction={announcer} />
      {supporters.length > 0 && (
        <>
          <div style={{ fontSize: 10, opacity: 0.6, margin: "8px 0 4px" }}>
            🤝 {t("cluster.supportedBy")}
          </div>
          {supporters.map((r) => (
            <UnionRow key={r.id} reaction={r} />
          ))}
        </>
      )}
    </div>
  );
}

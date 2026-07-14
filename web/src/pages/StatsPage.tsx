import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useStats, useEvents } from "../api/queries";
import type { TimeRange } from "../hooks/useFilterState";
import { AppShell } from "../components/layout";
import { TimeRangeTabs } from "../components/filters";
import { Spinner, ErrorState } from "../components/common";
import { KpiStrip, ActivityChart, AxisBreakdownBar, TopLocationsTable, TopClustersTable } from "../components/stats";
import styles from "./StatsPage.module.css";

const ACTIVITY_RANGES: TimeRange[] = ["7d", "30d", "all"];
const PERIOD_DAYS: Record<TimeRange, number | undefined> = { "24h": 1, "7d": 7, "30d": 30, all: undefined };

export function StatsPage() {
  const { t } = useTranslation();
  const { data: stats, isLoading, isError } = useStats();
  const recentEvents = useEvents({ limit: 5 });
  const [period, setPeriod] = useState<TimeRange>("30d");

  return (
    <AppShell>
      <div style={{ padding: "var(--space-3) var(--space-5)", borderBottom: "1px solid var(--color-border)", fontWeight: 700, fontSize: 13 }}>
        {t("stats.title")}
      </div>

      {isLoading && <Spinner />}
      {isError && <ErrorState />}

      {stats && (
        <>
          <KpiStrip
            totalEvents={stats.total_events}
            totalArticles={stats.total_articles}
            locationsCovered={stats.by_region.length}
            avgNewPerDay={stats.total_events / Math.max(stats.by_date.length, 1)}
          />

          <div className={styles.section}>
            <div className={styles.sectionHeader}>
              <span className={styles.sectionLabel}>{t("stats.activity")}</span>
              <TimeRangeTabs value={period} onChange={setPeriod} ranges={ACTIVITY_RANGES} />
            </div>
            <ActivityChart
              items={[...stats.by_date]
                .slice(0, PERIOD_DAYS[period] ?? stats.by_date.length)
                .reverse()}
            />
          </div>

          <div className={styles.grid2}>
            <div>
              <div className={styles.sectionLabel}>{t("stats.byActionForm")}</div>
              <div style={{ marginTop: 12 }}>
                <AxisBreakdownBar items={stats.by_action_form} />
              </div>
            </div>
            <div>
              <div className={styles.sectionLabel}>{t("stats.byThematicField")}</div>
              <div style={{ marginTop: 12 }}>
                <AxisBreakdownBar items={stats.by_thematic_field} />
              </div>
            </div>
          </div>

          <div className={styles.grid2}>
            <div>
              <div className={styles.sectionLabel}>{t("stats.byChannel")}</div>
              <div style={{ marginTop: 12 }}>
                <AxisBreakdownBar items={stats.by_channel} />
              </div>
            </div>
            <div>
              <div className={styles.sectionLabel}>{t("stats.byIntensity")}</div>
              <div style={{ marginTop: 12 }}>
                <AxisBreakdownBar items={stats.by_intensity} />
              </div>
            </div>
          </div>

          <div className={styles.section}>
            <div className={styles.sectionLabel}>{t("stats.topLocations")}</div>
            <div style={{ marginTop: 12 }}>
              <TopLocationsTable items={stats.by_region} />
            </div>
          </div>

          <div className={styles.section}>
            <div className={styles.sectionLabel}>{t("stats.recentlyUpdated")}</div>
            <div style={{ marginTop: 12 }}>
              {recentEvents.isLoading && <Spinner />}
              {recentEvents.data && <TopClustersTable events={recentEvents.data} />}
            </div>
          </div>
        </>
      )}
    </AppShell>
  );
}

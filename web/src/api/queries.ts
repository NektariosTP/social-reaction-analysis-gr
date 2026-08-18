import { useQuery } from "@tanstack/react-query";
import "./client";
import {
  eventsGeojsonEventsGeojsonGet,
  getEventEventsEventIdGet,
  getStatsStatsGet,
  listEventsEventsGet,
  listMunicipalitiesBoundariesMunicipalitiesGet,
  listPeripheriesBoundariesPeripheriesGet,
} from "../client/sdk.gen";
import type { EventSummary } from "../client/types.gen";
import { canonicalRegion } from "../i18n/regions";

async function unwrap<T>(result: Promise<{ data?: T; error?: unknown }>): Promise<T> {
  const { data, error } = await result;
  if (error !== undefined) throw error;
  if (data === undefined) throw new Error("Empty response");
  return data;
}

export interface EventFilters {
  actionForms?: string[];
  thematicFields?: string[];
  channel?: string;
  intensities?: string[];
  regionCode?: string;
  municipality?: string;
  dateFrom?: string;
  dateTo?: string;
  bbox?: string;
  limit?: number;
  offset?: number;
}

interface AxisTaggedEntity {
  action_forms: string[];
  thematic_fields: string[];
  intensity?: string | null;
  region_code?: string | null;
  municipality?: string | null;
}

/**
 * The API only accepts a single value per axis query param. For multi-select
 * axis filters we fetch a broader page (server-side on the filters that ARE
 * single-valued) and narrow client-side against the label arrays we already
 * have — simpler and more honest than firing N requests and merging them.
 * Shared between the /events list and /events/geojson results.
 */
export function applyClientFilters<T extends AxisTaggedEntity>(
  entities: T[],
  filters: Pick<EventFilters, "actionForms" | "thematicFields" | "intensities" | "regionCode" | "municipality">,
): T[] {
  let result = entities;
  if (filters.actionForms?.length) {
    const set = new Set(filters.actionForms);
    result = result.filter((e) => e.action_forms.some((f) => set.has(f)));
  }
  if (filters.thematicFields?.length) {
    const set = new Set(filters.thematicFields);
    result = result.filter((e) => e.thematic_fields.some((f) => set.has(f)));
  }
  if (filters.intensities?.length) {
    const set = new Set(filters.intensities);
    result = result.filter((e) => e.intensity && set.has(e.intensity));
  }
  if (filters.regionCode) {
    // region_code is language-inconsistent in the data (e.g. "Αττική" vs
    // "Attica") — canonicalise both sides so drill-down doesn't drop events.
    const target = canonicalRegion(filters.regionCode);
    result = result.filter((e) => canonicalRegion(e.region_code) === target);
  }
  if (filters.municipality) {
    result = result.filter((e) => e.municipality === filters.municipality);
  }
  return result;
}

export function useEvents(filters: EventFilters = {}) {
  return useQuery({
    queryKey: ["events", filters],
    queryFn: async () => {
      const events = await unwrap(
        listEventsEventsGet({
          query: {
            channel: filters.channel ?? null,
            region_code: filters.regionCode ?? null,
            municipality: filters.municipality ?? null,
            date_from: filters.dateFrom ?? null,
            date_to: filters.dateTo ?? null,
            bbox: filters.bbox ?? null,
            limit: filters.limit ?? 100,
            offset: filters.offset ?? 0,
          },
        }),
      );
      return applyClientFilters(events, filters);
    },
  });
}

export function useEvent(id: string | undefined) {
  return useQuery({
    queryKey: ["event", id],
    queryFn: () => unwrap(getEventEventsEventIdGet({ path: { event_id: id! } })),
    enabled: !!id,
  });
}

export function useEventsGeoJSON(filters: Pick<EventFilters, "channel"> = {}) {
  return useQuery({
    queryKey: ["events-geojson", filters],
    queryFn: () =>
      unwrap(
        eventsGeojsonEventsGeojsonGet({
          query: { channel: filters.channel ?? null },
        }),
      ),
  });
}

export function useStats() {
  return useQuery({
    queryKey: ["stats"],
    queryFn: () => unwrap(getStatsStatsGet({})),
  });
}

/** Count of events first-seen in the last hour — backs the "+N new · last hour" KPI. */
export function useRecentEventsCount() {
  return useQuery({
    queryKey: ["events-recent-count"],
    queryFn: async () => {
      const sinceIso = new Date(Date.now() - 3_600_000).toISOString();
      const events = await unwrap(
        listEventsEventsGet({ query: { date_from: sinceIso, limit: 200 } }),
      );
      return events.length;
    },
    refetchInterval: 60_000,
  });
}

/** Splits ongoing events into panhellenic (is_national) vs the rest, preserving order. */
export function partitionByNational(events: EventSummary[]): {
  panhellenic: EventSummary[];
  other: EventSummary[];
} {
  const panhellenic: EventSummary[] = [];
  const other: EventSummary[] = [];
  for (const e of events) (e.is_national ? panhellenic : other).push(e);
  return { panhellenic, other };
}

/** Events scheduled for today (Athens). Filter-independent — the temporal block always shows all. */
export function useOngoingEvents() {
  return useQuery({
    queryKey: ["events-ongoing"],
    queryFn: () =>
      unwrap(listEventsEventsGet({ query: { temporal_status: "today", limit: 100 } })),
  });
}

/** Upcoming events, soonest first. Filter-independent. */
export function useUpcomingEvents() {
  return useQuery({
    queryKey: ["events-upcoming"],
    queryFn: () =>
      unwrap(
        listEventsEventsGet({
          query: { temporal_status: "upcoming", order_by: "event_time", limit: 100 },
        }),
      ),
  });
}

/** All 13 periphery outlines (simplified). Immutable geometry — cached indefinitely. */
export function usePeripheryBoundaries() {
  return useQuery({
    queryKey: ["boundaries", "peripheries"],
    queryFn: () => unwrap(listPeripheriesBoundariesPeripheriesGet({})),
    staleTime: Infinity,
  });
}

/** Municipalities of one periphery (simplified). Disabled until a periphery is selected. */
export function useMunicipalityBoundaries(region: string | null) {
  return useQuery({
    queryKey: ["boundaries", "municipalities", region],
    queryFn: () =>
      unwrap(listMunicipalitiesBoundariesMunicipalitiesGet({ query: { periphery: region! } })),
    enabled: !!region,
    staleTime: Infinity,
  });
}

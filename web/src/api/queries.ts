import { keepPreviousData, useQuery } from "@tanstack/react-query";
import "./client";
import {
  eventsGeojsonEventsGeojsonGet,
  getEventEventsEventIdGet,
  listEventsEventsGet,
} from "../client/sdk.gen";

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
  intensity?: string;
  eventDate?: string;
  windowDays?: number;
  bbox?: string;
  limit?: number;
  offset?: number;
}

interface AxisTaggedEntity {
  action_forms: string[];
  thematic_fields: string[];
}

/**
 * The API only accepts a single value per axis query param. Action/theme are
 * genuinely multi-select, so for those we fetch a broader page (server-side
 * on the filters that ARE single-valued) and narrow client-side against the
 * label arrays we already have — simpler and more honest than firing N
 * requests and merging them. Channel and intensity are single-valued per
 * event, so they go straight through as server-side query params instead.
 * Shared between the /events list and /events/geojson results.
 */
export function applyClientFilters<T extends AxisTaggedEntity>(
  entities: T[],
  filters: Pick<EventFilters, "actionForms" | "thematicFields">,
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
            intensity: filters.intensity ?? null,
            event_date: filters.eventDate ?? null,
            window_days: filters.windowDays ?? null,
            bbox: filters.bbox ?? null,
            limit: filters.limit ?? 100,
            offset: filters.offset ?? 0,
          },
        }),
      );
      return applyClientFilters(events, filters);
    },
    // Keep the prior results visible while a new day/range query is in flight so
    // MainView never swaps MapView for a Spinner — otherwise the MapLibre instance
    // is torn down and rebuilt on every slider/range change (the "whole map
    // re-renders" bug). Markers update; the map itself stays mounted.
    placeholderData: keepPreviousData,
  });
}

export function useEvent(id: string | undefined) {
  return useQuery({
    queryKey: ["event", id],
    queryFn: () => unwrap(getEventEventsEventIdGet({ path: { event_id: id! } })),
    enabled: !!id,
  });
}

export function useEventsGeoJSON(
  filters: Pick<EventFilters, "channel" | "intensity" | "eventDate" | "windowDays"> = {},
) {
  return useQuery({
    queryKey: ["events-geojson", filters],
    queryFn: () =>
      unwrap(
        eventsGeojsonEventsGeojsonGet({
          query: {
            channel: filters.channel ?? null,
            intensity: filters.intensity ?? null,
            event_date: filters.eventDate ?? null,
            window_days: filters.windowDays ?? null,
          },
        }),
      ),
    // See useEvents — keeps the map mounted across day/range changes.
    placeholderData: keepPreviousData,
  });
}

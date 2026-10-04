import { reactive } from "vue";
import { api } from "@/api/client";
import type { ExerciseHistory, Outing } from "@/types/lifting";

export interface HistoryEntry {
  loading: boolean;
  items: Outing[];
  total: number;
  error: string | null;
}

// Shared across views so Plan, Track and the add-exercise sheet don't refetch.
const cache = reactive(new Map<string, HistoryEntry>());

function cacheKey(title: string, limit: number, exclude: number | null) {
  return `${title}\u0000${limit}\u0000${exclude ?? ""}`;
}

/** Last few done outings of exercises by exact title. */
export function useExerciseHistory(options: { limit?: number; excludeSession?: () => number | null } = {}) {
  const limit = options.limit ?? 3;
  const exclude = () => options.excludeSession?.() ?? null;

  /** Start loading a title's history if it isn't cached. Resolves when it's there. */
  async function load(title: string): Promise<HistoryEntry | null> {
    const name = title.trim();
    if (!name) return null;
    const key = cacheKey(name, limit, exclude());
    const existing = cache.get(key);
    if (existing && !existing.error) return existing;

    cache.set(key, { loading: true, items: [], total: 0, error: null });
    const params = new URLSearchParams({ title: name, limit: String(limit) });
    const excluded = exclude();
    if (excluded !== null) params.set("exclude_session", String(excluded));
    const response = await api.get<ExerciseHistory>(`/api/lifting/exercises/history/?${params}`);
    const entry = cache.get(key)!;
    entry.loading = false;
    if (response.data) {
      entry.items = response.data.items;
      entry.total = response.data.total;
    } else {
      entry.error = response.error || "Couldn't load history";
    }
    return entry;
  }

  /** The cached entry for a title, or undefined if it hasn't been loaded. */
  function get(title: string): HistoryEntry | undefined {
    return cache.get(cacheKey(title.trim(), limit, exclude()));
  }

  return { load, get };
}

/** Forget cached history, e.g. after a session finishes and adds outings. */
export function clearExerciseHistory() {
  cache.clear();
}

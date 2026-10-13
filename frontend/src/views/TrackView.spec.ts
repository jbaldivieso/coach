import { describe, it, expect, vi, beforeEach } from "vitest";
import { mount, flushPromises } from "@vue/test-utils";
import { createRouter, createMemoryHistory, RouterView } from "vue-router";
import { createPinia, setActivePinia } from "pinia";
import TrackView from "./TrackView.vue";
import { useActiveSessionStore } from "@/stores/activeSession";
import type { Exercise, Session } from "@/types/lifting";

vi.mock("@/api/client", () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    fetchCsrfToken: vi.fn(),
  },
}));

// No AudioContext in the test DOM
vi.mock("@/utils/audio", () => ({ unlockAudio: vi.fn(), playAlarm: vi.fn(), vibrate: vi.fn() }));

import { api } from "@/api/client";

function exercise(id: number, title: string, done: boolean[], group: number | null = null): Exercise {
  return {
    id,
    title,
    sets: done.map((d) => ({ weight: 100, reps: 5, done: d })),
    rest_seconds: 90,
    comments: "",
    position: id,
    superset_group: group,
  };
}

function session(exercises: Exercise[]): Session {
  return {
    id: 1,
    title: "Upper A",
    date: "2026-01-23",
    comments: "",
    status: "active",
    started_at: "2026-01-23T07:31:00Z",
    finished_at: null,
    exercises,
  };
}

const placeholder = { template: "<div/>" };

async function mountTrack(exercises: Exercise[]) {
  vi.mocked(api.get).mockImplementation((url: string) => {
    if (url.includes("/exercises/history/"))
      return Promise.resolve({ data: { title: "", items: [], total: 0, has_more: false }, error: null });
    return Promise.resolve({ data: session(exercises), error: null });
  });
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/", name: "home", component: placeholder },
      { path: "/track/:id", name: "track", component: TrackView },
      { path: "/track/:id/edit", name: "track-edit", component: placeholder },
      { path: "/track/:id/finish", name: "track-finish", component: placeholder },
      { path: "/session/:id", name: "session-detail", component: placeholder },
      { path: "/exercise/:title", name: "exercise-history", component: placeholder },
      { path: "/changelog", name: "changelog", component: placeholder },
    ],
  });
  await router.push("/track/1");
  await router.isReady();
  const wrapper = mount(RouterView, { global: { plugins: [router] }, attachTo: document.body });
  await flushPromises();
  return { wrapper, router, store: useActiveSessionStore() };
}

describe("TrackView", () => {
  /** Resolves the save that's in flight, as the server answering. */
  let answer: (ok: boolean) => void;

  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    const memory = new Map<string, string>();
    vi.stubGlobal("localStorage", {
      getItem: (k: string) => memory.get(k) ?? null,
      setItem: (k: string, v: string) => memory.set(k, v),
      removeItem: (k: string) => memory.delete(k),
    });
    // A slow connection: the save hangs until the test answers it
    vi.mocked(api.put).mockImplementation(
      () => new Promise((resolve) => (answer = (ok) => resolve({ data: ok ? {} : null, error: ok ? null : "Request failed" }))),
    );
  });

  it("starts the rest on the Done tap, without waiting for the save", async () => {
    const { wrapper, store } = await mountTrack([exercise(10, "Bench", [false, false])]);
    await wrapper.find(".dock button").trigger("click");
    await flushPromises();

    expect(api.put).toHaveBeenCalledTimes(1);
    expect(store.rest?.total).toBe(90);
    expect(wrapper.find(".rest").exists()).toBe(true);
    expect(store.exercises[0]!.sets[0]!.done).toBe(true);

    // The save failing later puts the set in the retry banner; the rest carries on
    answer(false);
    await flushPromises();
    expect(store.unsaved).toHaveLength(1);
    expect(store.rest).not.toBeNull();
    wrapper.unmount();
  });

  it("ignores a double tap instead of logging the next set", async () => {
    // A superset mid-round: no rest screen comes up to cover the button
    const { wrapper, store } = await mountTrack([exercise(10, "Bench", [false], 1), exercise(11, "Row", [false], 1), exercise(12, "Curl", [false])]);
    await wrapper.find(".dock button").trigger("click");
    await wrapper.find(".dock button").trigger("click");
    await flushPromises();

    expect(store.exercises[0]!.sets[0]!.done).toBe(true);
    expect(store.exercises[1]!.sets[0]!.done).toBe(false);
    wrapper.unmount();
  });

  it("waits for the last set to save before going to Finish", async () => {
    const { wrapper, router } = await mountTrack([exercise(10, "Bench", [true, false])]);
    await wrapper.find(".dock button").trigger("click");
    await flushPromises();
    expect(router.currentRoute.value.name).toBe("track");

    answer(true);
    await flushPromises();
    expect(router.currentRoute.value.name).toBe("track-finish");
    wrapper.unmount();
  });
});

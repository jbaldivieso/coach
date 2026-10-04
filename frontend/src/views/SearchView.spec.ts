import { describe, it, expect, vi, beforeEach } from "vitest";
import { mount, flushPromises } from "@vue/test-utils";
import { createRouter, createMemoryHistory } from "vue-router";
import { createPinia, setActivePinia } from "pinia";
import SearchView from "./SearchView.vue";
import type { SearchResponse } from "@/types/lifting";
import { toISODate } from "@/utils/format";

vi.mock("@/api/client", () => ({
  api: { get: vi.fn(), post: vi.fn(), fetchCsrfToken: vi.fn() },
}));

import { api } from "@/api/client";

function daysBack(n: number) {
  const d = new Date();
  d.setDate(d.getDate() - n);
  return toISODate(d);
}

const placeholder = { template: "<div/>" };

async function mountAt(url: string) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/", name: "home", component: placeholder },
      { path: "/search", name: "search", component: SearchView },
      { path: "/session/:id", name: "session-detail", component: placeholder },
      { path: "/exercise/:title", name: "exercise-history", component: placeholder },
      { path: "/changelog", name: "changelog", component: placeholder },
      { path: "/login", name: "login", component: placeholder },
    ],
  });
  await router.push(url);
  await router.isReady();
  const wrapper = mount(SearchView, { global: { plugins: [router] } });
  await flushPromises();
  return { wrapper, router };
}

describe("SearchView", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it("answers when a matching session was last done", async () => {
    const data: SearchResponse = {
      sessions: [
        { id: 9, title: "Lower B", date: daysBack(22) },
        { id: 4, title: "Lower A", date: daysBack(36) },
      ],
      exercises: [{ title: "Lower back extension", count: 4, last_date: daysBack(36) }],
      last_session: { id: 9, title: "Lower B", date: daysBack(22) },
    };
    vi.mocked(api.get).mockResolvedValue({ data, error: null });
    const { wrapper } = await mountAt("/search?q=lower");

    expect(api.get).toHaveBeenCalledWith("/api/lifting/search/?q=lower");
    expect(wrapper.find(".answer").text()).toContain("22 days ago");
    expect(wrapper.find(".answer").attributes("href")).toBe("/session/9");
    expect(wrapper.findAll(".list")[0]!.findAll(".row")).toHaveLength(2);
    expect(wrapper.text()).toContain("Lower back extension");
    expect(wrapper.text()).toContain("4 times");
  });

  it("falls back to the top exercise when no session title matches", async () => {
    vi.mocked(api.get).mockResolvedValue({
      data: { sessions: [], exercises: [{ title: "Bench", count: 25, last_date: daysBack(2) }], last_session: null },
      error: null,
    });
    const { wrapper } = await mountAt("/search?q=bench");
    expect(wrapper.find(".answer").text()).toContain("Last Bench");
    expect(wrapper.find(".answer").attributes("href")).toBe("/exercise/Bench");
  });

  it("says when nothing matches", async () => {
    vi.mocked(api.get).mockResolvedValue({ data: { sessions: [], exercises: [], last_session: null }, error: null });
    const { wrapper } = await mountAt("/search?q=zzz");
    expect(wrapper.text()).toContain("Nothing matches");
  });

  it("searches as you type, and keeps the query in the URL", async () => {
    vi.useFakeTimers();
    vi.mocked(api.get).mockResolvedValue({ data: { sessions: [], exercises: [], last_session: null }, error: null });
    const { wrapper, router } = await mountAt("/search");
    expect(api.get).not.toHaveBeenCalled();
    await wrapper.find("input").setValue("squat");
    vi.advanceTimersByTime(300);
    vi.useRealTimers();
    await flushPromises();
    expect(api.get).toHaveBeenCalledWith("/api/lifting/search/?q=squat");
    expect(router.currentRoute.value.query.q).toBe("squat");
  });
});

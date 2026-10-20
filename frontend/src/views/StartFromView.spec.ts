import { describe, it, expect, vi, beforeEach } from "vitest";
import { mount, flushPromises } from "@vue/test-utils";
import { createRouter, createMemoryHistory } from "vue-router";
import { createPinia, setActivePinia } from "pinia";
import StartFromView from "./StartFromView.vue";
import type { Template, PaginatedSessions } from "@/types/lifting";

vi.mock("@/api/client", () => ({
  api: { get: vi.fn(), post: vi.fn() },
}));

import { api } from "@/api/client";

function template(id: number, title: string, exercises: string[]): Template {
  return {
    id,
    title,
    comments: "",
    archived_at: null,
    created_at: "2026-10-01T00:00:00Z",
    updated_at: "2026-10-01T00:00:00Z",
    exercises: exercises.map((t, i) => ({
      id: id * 10 + i,
      title: t,
      sets: [{ weight: null, reps: 5 }],
      rest_seconds: 90,
      comments: "",
      position: i,
      superset_group: null,
    })),
  };
}

const sessions: PaginatedSessions = {
  items: [
    {
      id: 3,
      title: "Upper A",
      date: "2026-10-10",
      comments: "",
      status: "done",
      started_at: null,
      finished_at: null,
      template_id: null,
      exercises: [],
    },
  ],
  total: 1,
  has_more: false,
};

const placeholder = { template: "<div/>" };

async function mountWith(templates: Template[]) {
  vi.mocked(api.get).mockImplementation((url: string) =>
    Promise.resolve(
      url.startsWith("/api/lifting/templates/")
        ? { data: templates, error: null }
        : { data: sessions, error: null },
    ),
  );
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/", name: "home", component: placeholder },
      { path: "/start-from", name: "start-from", component: StartFromView },
      { path: "/plan/new", name: "plan-new", component: placeholder },
      { path: "/changelog", name: "changelog", component: placeholder },
      { path: "/login", name: "login", component: placeholder },
    ],
  });
  await router.push("/start-from");
  await router.isReady();
  const wrapper = mount(StartFromView, { global: { plugins: [router] } });
  await flushPromises();
  return wrapper;
}

describe("StartFromView", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it("lists templates above past sessions, linking to a plan from each", async () => {
    const wrapper = await mountWith([template(7, "Week 2 · Lower", ["Squat", "RDL"])]);
    expect(wrapper.findAll(".eyebrow").map((h) => h.text())).toEqual(["Templates", "Past sessions"]);
    const rows = wrapper.findAll("a.row");
    expect(rows.map((r) => r.find(".row-title").text())).toEqual(["Week 2 · Lower", "Upper A"]);
    expect(rows[0]!.attributes("href")).toBe("/plan/new?template=7");
    expect(rows[0]!.find(".row-date").exists()).toBe(false);
    expect(rows[1]!.find(".row-date").exists()).toBe(true);
    expect(api.get).toHaveBeenCalledTimes(2);
  });

  it("filters templates by title and exercise without refetching them", async () => {
    const wrapper = await mountWith([template(7, "Week 2 · Lower", ["Squat"]), template(8, "Push day", ["Bench"])]);
    const titles = () => wrapper.findAll(".templates .row-title").map((r) => r.text());
    await wrapper.find('input[type="search"]').setValue("bench");
    expect(titles()).toEqual(["Push day"]);
    await wrapper.find('input[type="search"]').setValue("lower");
    expect(titles()).toEqual(["Week 2 · Lower"]);
    await wrapper.find('input[type="search"]').setValue("deadlift");
    expect(wrapper.find(".templates").exists()).toBe(false);
    expect(wrapper.find(".eyebrow").exists()).toBe(false);
    const templateCalls = vi.mocked(api.get).mock.calls.filter(([url]) => url.startsWith("/api/lifting/templates/"));
    expect(templateCalls).toHaveLength(1);
  });

  it("says no past sessions match when only templates do", async () => {
    const wrapper = await mountWith([template(7, "Week 2 · Lower", ["Squat"])]);
    vi.mocked(api.get).mockResolvedValue({ data: { items: [], total: 0, has_more: false }, error: null });
    await wrapper.find('input[type="search"]').setValue("squat");
    await new Promise((r) => setTimeout(r, 250));
    await flushPromises();
    expect(wrapper.find(".results .empty").text()).toBe('No past sessions match "squat".');
  });

  it("has no templates section when there are none", async () => {
    const wrapper = await mountWith([]);
    expect(wrapper.find(".templates").exists()).toBe(false);
    expect(wrapper.find(".eyebrow").exists()).toBe(false);
    expect(wrapper.findAll("a.row")).toHaveLength(1);
  });
});

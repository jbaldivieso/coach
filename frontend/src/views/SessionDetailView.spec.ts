import { describe, it, expect, vi, beforeEach } from "vitest";
import { mount, flushPromises } from "@vue/test-utils";
import { createRouter, createMemoryHistory } from "vue-router";
import { createPinia, setActivePinia } from "pinia";
import SessionDetailView from "./SessionDetailView.vue";
import type { Session } from "@/types/lifting";

vi.mock("@/api/client", () => ({
  api: { get: vi.fn(), delete: vi.fn(), post: vi.fn(), fetchCsrfToken: vi.fn() },
}));

import { api } from "@/api/client";

const mockSession: Session = {
  id: 1,
  title: "Upper A",
  date: "2024-01-15",
  comments: "Good session",
  status: "done",
  started_at: null,
  finished_at: null,
  exercises: [
    {
      id: 1,
      title: "Bench Press",
      sets: [
        { weight: 135, reps: 10, done: true },
        { weight: 135, reps: 8, done: true },
      ],
      rest_seconds: 90,
      comments: "Felt strong",
      position: 0,
      superset_group: null,
    },
    {
      id: 2,
      title: "Flyes",
      sets: [{ weight: 20, reps: 12, done: true }],
      rest_seconds: 60,
      comments: "",
      position: 1,
      superset_group: 1,
    },
    {
      id: 3,
      title: "Pull-ups",
      sets: [{ weight: null, reps: 10, done: true }],
      rest_seconds: 60,
      comments: "",
      position: 2,
      superset_group: 1,
    },
  ],
};

const placeholder = { template: "<div/>" };

async function mountView(session: Session | null, error: string | null = null) {
  vi.mocked(api.get).mockResolvedValue({ data: session, error });
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/", name: "home", component: placeholder },
      { path: "/session/:id", name: "session-detail", component: SessionDetailView },
      { path: "/session/:id/edit", name: "session-edit", component: placeholder },
      { path: "/plan/new", name: "plan-new", component: placeholder },
      { path: "/plan/:id", name: "plan-edit", component: placeholder },
      { path: "/track/:id", name: "track", component: placeholder },
      { path: "/exercise/:title", name: "exercise-history", component: placeholder },
      { path: "/changelog", name: "changelog", component: placeholder },
      { path: "/login", name: "login", component: placeholder },
    ],
  });
  await router.push("/session/1");
  await router.isReady();
  const wrapper = mount(SessionDetailView, { global: { plugins: [router] } });
  await flushPromises();
  return { wrapper, router };
}

describe("SessionDetailView", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
  });

  it("shows the date and title in the bar, and comments", async () => {
    const { wrapper } = await mountView(mockSession);
    expect(wrapper.find(".appbar-title").text()).toBe("Mon Jan 15 · Upper A");
    expect(wrapper.text()).toContain("Good session");
    expect(wrapper.text()).toContain("Felt strong");
  });

  it("links every exercise name to its history", async () => {
    const { wrapper } = await mountView(mockSession);
    const hrefs = wrapper.findAll("a.link").map((a) => a.attributes("href"));
    expect(hrefs).toEqual(["/exercise/Bench%20Press", "/exercise/Flyes", "/exercise/Pull-ups"]);
  });

  it("groups a superset under one rest", async () => {
    const { wrapper } = await mountView(mockSession);
    const ss = wrapper.find(".ss");
    expect(ss.text()).toContain("Superset");
    expect(ss.text()).toContain("rest 1:00");
    expect(ss.findAll(".sx")).toHaveLength(2);
    expect(ss.text()).toContain("BW");
  });

  it("offers Start from this and edit", async () => {
    const { wrapper } = await mountView(mockSession);
    expect(wrapper.find(".dock a").attributes("href")).toBe("/plan/new?from=1");
    expect(wrapper.find('[aria-label="Edit session"]').attributes("href")).toBe("/session/1/edit");
  });

  it("sends an active session to Track", async () => {
    const { router } = await mountView({ ...mockSession, status: "active" });
    expect(router.currentRoute.value.name).toBe("track");
  });

  it("shows an error with retry", async () => {
    const { wrapper } = await mountView(null, "Session not found");
    expect(wrapper.text()).toContain("Session not found");
    vi.mocked(api.get).mockResolvedValue({ data: mockSession, error: null });
    await wrapper.find('[data-testid="retry-button"]').trigger("click");
    await flushPromises();
    expect(wrapper.text()).toContain("Bench Press");
  });
});

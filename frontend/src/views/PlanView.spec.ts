import { describe, it, expect, vi, beforeEach } from "vitest";
import { mount, flushPromises } from "@vue/test-utils";
import { createRouter, createMemoryHistory, RouterView } from "vue-router";
import { createPinia, setActivePinia } from "pinia";
import PlanView from "./PlanView.vue";
import type { Session } from "@/types/lifting";

vi.mock("@/api/client", () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
    fetchCsrfToken: vi.fn(),
  },
}));

import { api } from "@/api/client";

const source: Session = {
  id: 1,
  title: "Upper A",
  date: "2026-01-18",
  comments: "Old session note",
  status: "done",
  started_at: null,
  finished_at: null,
  exercises: [
    {
      id: 10,
      title: "Bench",
      sets: [
        { weight: 150, reps: 5, done: true },
        { weight: 155, reps: 4, done: true },
      ],
      rest_seconds: 240,
      comments: "Doable.",
      position: 0,
      superset_group: null,
    },
    {
      id: 11,
      title: "Lat raises",
      sets: [{ weight: 30, reps: 12, done: true }],
      rest_seconds: 90,
      comments: "",
      position: 1,
      superset_group: null,
    },
  ],
};

const placeholder = { template: "<div/>" };

function makeRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/", name: "home", component: placeholder },
      { path: "/plan/new", name: "plan-new", component: PlanView },
      { path: "/track/:id", name: "track", component: placeholder },
      { path: "/session/:id", name: "session-detail", component: placeholder },
      { path: "/exercise/:title", name: "exercise-history", component: placeholder },
      { path: "/changelog", name: "changelog", component: placeholder },
      { path: "/login", name: "login", component: placeholder },
    ],
  });
}

async function mountFrom() {
  const router = makeRouter();
  await router.push("/plan/new?from=1");
  await router.isReady();
  // Inside a RouterView, so the leave guard is live
  const wrapper = mount(RouterView, { global: { plugins: [router] }, attachTo: document.body });
  await flushPromises();
  return { wrapper, router };
}

function lastPostBody() {
  const calls = vi.mocked(api.post).mock.calls.filter(([url]) => url.includes("with-exercises"));
  return calls[calls.length - 1]![1] as { status: string; comments: string; exercises: { title: string; sets: unknown[]; superset_group: number | null; comments: string }[] };
}

describe("PlanView", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url.startsWith("/api/lifting/sessions/1/")) return Promise.resolve({ data: source, error: null });
      if (url.includes("/exercises/history/"))
        return Promise.resolve({ data: { title: "", items: [], total: 0, has_more: false }, error: null });
      return Promise.resolve({ data: null, error: null });
    });
    vi.mocked(api.post).mockResolvedValue({ data: { ...source, id: 5, status: "active" }, error: null });
  });

  it("starts from a past session as undone targets without its comments", async () => {
    const { wrapper } = await mountFrom();
    expect(wrapper.text()).toContain("from Jan 18");
    await wrapper.findAll(".dock button")[0]!.trigger("click");
    await flushPromises();
    const body = lastPostBody();
    expect(body.status).toBe("active");
    expect(body.exercises.map((e) => e.title)).toEqual(["Bench", "Lat raises"]);
    expect(body.exercises[0]!.sets).toEqual([
      { weight: 150, reps: 5, done: false },
      { weight: 155, reps: 4, done: false },
    ]);
    expect(body.exercises[0]!.comments).toBe("");
    wrapper.unmount();
  });

  it("save for later creates a planned session", async () => {
    const { wrapper, router } = await mountFrom();
    await wrapper.findAll(".dock button")[1]!.trigger("click");
    await flushPromises();
    expect(lastPostBody().status).toBe("planned");
    expect(router.currentRoute.value.name).toBe("home");
    wrapper.unmount();
  });

  it("set-count stepper adds a copy of the last set", async () => {
    const { wrapper } = await mountFrom();
    await wrapper.find('[aria-label="One more set"]').trigger("click");
    expect(wrapper.find(".ex").findAll(".setchips .chip")).toHaveLength(3);
    await wrapper.findAll(".dock button")[0]!.trigger("click");
    await flushPromises();
    expect(lastPostBody().exercises[0]!.sets[2]).toEqual({ weight: 155, reps: 4, done: false });
    wrapper.unmount();
  });

  it("copy set 1 to all", async () => {
    const { wrapper } = await mountFrom();
    await wrapper.find(".ex .setchips .chip").trigger("click");
    await wrapper.find(".copydown").trigger("click");
    await wrapper.findAll(".dock button")[0]!.trigger("click");
    await flushPromises();
    expect(lastPostBody().exercises[0]!.sets).toEqual([
      { weight: 150, reps: 5, done: false },
      { weight: 150, reps: 5, done: false },
    ]);
    wrapper.unmount();
  });

  it("links a superset from the exercise menu, evening out set counts", async () => {
    const { wrapper } = await mountFrom();
    await wrapper.find('[aria-label="Exercise options"]').trigger("click");
    const link = Array.from(document.querySelectorAll<HTMLButtonElement>(".action")).find((b) =>
      b.textContent?.includes("Superset with Lat raises"),
    );
    expect(link).toBeDefined();
    link!.click();
    await flushPromises();
    expect(wrapper.find(".ss").exists()).toBe(true);
    expect(wrapper.find(".ss-title").text()).toContain("2 rounds");
    await wrapper.findAll(".dock button")[0]!.trigger("click");
    await flushPromises();
    const exercises = lastPostBody().exercises;
    expect(exercises.map((e) => e.superset_group)).toEqual([1, 1]);
    expect(exercises[1]!.sets).toHaveLength(2);
    wrapper.unmount();
  });

  it("won't save without a title", async () => {
    const { wrapper } = await mountFrom();
    const title = wrapper.find('input[aria-label="Session title"]');
    await title.setValue("");
    await title.trigger("input");
    await wrapper.findAll(".dock button")[0]!.trigger("click");
    await flushPromises();
    expect(api.post).not.toHaveBeenCalledWith("/api/lifting/sessions/with-exercises/", expect.anything());
    expect(wrapper.text()).toContain("Give it a title");
    wrapper.unmount();
  });

  it("folds the open exercise, and a tap opens it again", async () => {
    Element.prototype.scrollIntoView = vi.fn();
    const { wrapper } = await mountFrom();
    expect(wrapper.findAll(".ex")).toHaveLength(1);
    await wrapper.find('[aria-label="Fold"]').trigger("click");
    expect(wrapper.find(".ex").exists()).toBe(false);
    const collapsed = wrapper.findAll(".collapsed");
    expect(collapsed).toHaveLength(2);
    expect(collapsed[0]!.classes()).toContain("is-just");
    await collapsed[1]!.trigger("click");
    expect(wrapper.find(".ex input[aria-label='Exercise name']").element).toHaveProperty("value", "Lat raises");
    wrapper.unmount();
  });

  it("a collapsed exercise shows its plan and rest, not last time", async () => {
    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url.startsWith("/api/lifting/sessions/1/")) return Promise.resolve({ data: source, error: null });
      if (url.includes("/exercises/history/"))
        return Promise.resolve({
          data: { title: "", items: [{ id: 3, session_id: 3, date: "2026-01-10", title: "Upper A", sets: [{ weight: 25, reps: 15, done: true }], rest_seconds: 90, comments: "" }], total: 1, has_more: false },
          error: null,
        });
      return Promise.resolve({ data: null, error: null });
    });
    const { wrapper } = await mountFrom();
    const card = wrapper.find(".collapsed");
    expect(card.text()).toContain("Lat raises");
    expect(card.text()).toContain("1:30");
    expect(card.text()).toContain("30");
    expect(card.text()).not.toContain("Jan 10");
    expect(card.text()).not.toContain("25");
    wrapper.unmount();
  });

  it("has a session note under the date, saved with a new plan", async () => {
    const { wrapper } = await mountFrom();
    const note = wrapper.find('textarea[aria-label="Session note"]');
    expect(note.attributes("placeholder")).toBe("Session note");
    expect((note.element as HTMLTextAreaElement).value).toBe("");
    await note.setValue("Shoulder's cranky");
    await wrapper.findAll(".dock button")[1]!.trigger("click");
    await flushPromises();
    expect(lastPostBody().comments).toBe("Shoulder's cranky");
    wrapper.unmount();
  });

  it("asks before leaving with unsaved changes", async () => {
    const { wrapper, router } = await mountFrom();
    await wrapper.find('input[aria-label="Session title"]').setValue("Upper B");
    const confirm = vi.fn(() => false);
    vi.stubGlobal("confirm", confirm);
    await router.push("/");
    expect(confirm).toHaveBeenCalledWith("Discard your changes?");
    expect(router.currentRoute.value.name).toBe("plan-new");
    vi.unstubAllGlobals();
    wrapper.unmount();
  });
});

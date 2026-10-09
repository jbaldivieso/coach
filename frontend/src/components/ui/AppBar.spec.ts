import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { mount, flushPromises } from "@vue/test-utils";
import { createRouter, createMemoryHistory } from "vue-router";
import { createPinia, setActivePinia } from "pinia";
import AppBar from "./AppBar.vue";

const placeholder = { template: "<div/>" };

async function mountBar(props: Record<string, unknown>, path = "/history/year") {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: "/", name: "home", component: placeholder },
      { path: "/history/year", name: "year", component: placeholder },
      { path: "/search", name: "search", component: placeholder },
    ],
  });
  await router.push(path);
  await router.isReady();
  const wrapper = mount(AppBar, { props, global: { plugins: [router] } });
  await flushPromises();
  return { wrapper, router };
}

describe("AppBar", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    window.history.replaceState(null, "");
  });
  afterEach(() => window.history.replaceState(null, ""));

  it("has COACH linking home on every screen", async () => {
    const { wrapper } = await mountBar({ title: "Past year" });
    const mark = wrapper.find('a[aria-label="Home"]');
    expect(mark.text()).toBe("Coach");
    expect(mark.attributes("href")).toBe("/");
    expect(wrapper.find(".vrule").exists()).toBe(true);
  });

  it("is the title on Home, with no rule", async () => {
    const { wrapper } = await mountBar({}, "/");
    expect(wrapper.find("h1 a[aria-label='Home']").exists()).toBe(true);
    expect(wrapper.find(".vrule").exists()).toBe(false);
  });

  it("hides back when it would only go home", async () => {
    const { wrapper } = await mountBar({ title: "Past year", back: "/" });
    expect(wrapper.find('[aria-label="Back"]').exists()).toBe(false);
  });

  it("shows back for a route other than home", async () => {
    const { wrapper } = await mountBar({ title: "October", back: "/history/year" });
    expect(wrapper.find('[aria-label="Back"]').exists()).toBe(true);
  });

  it("shows back when history goes somewhere other than home", async () => {
    window.history.replaceState({ back: "/search?q=bench" }, "");
    const { wrapper } = await mountBar({ title: "Upper A", back: "/" });
    expect(wrapper.find('[aria-label="Back"]').exists()).toBe(true);
  });

  it("shows back for a function", async () => {
    const { wrapper } = await mountBar({ title: "Rest", back: () => {} });
    expect(wrapper.find('[aria-label="Back"]').exists()).toBe(true);
  });
});

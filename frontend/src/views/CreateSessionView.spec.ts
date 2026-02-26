import { describe, it, expect, vi, beforeEach } from "vitest";
import { mount, flushPromises } from "@vue/test-utils";
import { createRouter, createMemoryHistory } from "vue-router";
import CreateSessionView from "./CreateSessionView.vue";

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

const router = createRouter({
  history: createMemoryHistory(),
  routes: [
    { path: "/sessions/new", name: "create-session", component: CreateSessionView },
    { path: "/session/:id", name: "session-detail", component: { template: "<div/>" } },
    { path: "/", name: "home", component: { template: "<div/>" } },
  ],
});

describe("CreateSessionView - exercise title autocomplete", () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    vi.mocked(api.get).mockResolvedValue({ data: null, error: null });
    await router.push("/sessions/new");
    await router.isReady();
  });

  function mountComponent() {
    return mount(CreateSessionView, {
      global: { plugins: [router] },
    });
  }

  function getSuggestionsMock(suggestions: string[]) {
    return vi.mocked(api.get).mockImplementation((url: string) => {
      if (url.includes("/exercises/autocomplete/")) {
        return Promise.resolve({ data: { suggestions }, error: null });
      }
      return Promise.resolve({ data: null, error: null });
    });
  }

  it("renders the exercise title input", () => {
    const wrapper = mountComponent();
    const input = wrapper.find('input[placeholder="e.g., Bench Press"]');
    expect(input.exists()).toBe(true);
  });

  it("does not show dropdown before typing", () => {
    const wrapper = mountComponent();
    expect(wrapper.find(".exercise-title-dropdown").exists()).toBe(false);
  });

  it("calls autocomplete API after debounce when typing", async () => {
    getSuggestionsMock(["Bench Press"]);
    const wrapper = mountComponent();

    const input = wrapper.find('input[placeholder="e.g., Bench Press"]');
    await input.setValue("bench");
    await input.trigger("input");

    await new Promise((r) => setTimeout(r, 250));
    await flushPromises();

    expect(api.get).toHaveBeenCalledWith(
      expect.stringContaining("/exercises/autocomplete/?q=bench"),
    );
  });

  it("shows dropdown with suggestions", async () => {
    getSuggestionsMock(["Bench Press", "Bench Fly"]);
    const wrapper = mountComponent();

    const input = wrapper.find('input[placeholder="e.g., Bench Press"]');
    await input.trigger("focus");
    await input.setValue("bench");
    await input.trigger("input");

    await new Promise((r) => setTimeout(r, 250));
    await flushPromises();

    const items = wrapper.findAll(".exercise-title-item");
    expect(items.length).toBe(2);
    expect(items[0]?.text()).toBe("Bench Press");
    expect(items[1]?.text()).toBe("Bench Fly");
  });

  it("fills title and hides dropdown on suggestion click", async () => {
    getSuggestionsMock(["Bench Press"]);
    const wrapper = mountComponent();

    const input = wrapper.find('input[placeholder="e.g., Bench Press"]');
    await input.trigger("focus");
    await input.setValue("ben");
    await input.trigger("input");

    await new Promise((r) => setTimeout(r, 250));
    await flushPromises();

    await wrapper.find(".exercise-title-item").trigger("mousedown");
    await flushPromises();

    expect((input.element as HTMLInputElement).value).toBe("Bench Press");
    expect(wrapper.find(".exercise-title-dropdown").exists()).toBe(false);
  });

  it("navigates suggestions with arrow keys and selects with Enter", async () => {
    getSuggestionsMock(["Bench Press", "Bench Fly"]);
    const wrapper = mountComponent();

    const input = wrapper.find('input[placeholder="e.g., Bench Press"]');
    await input.trigger("focus");
    await input.setValue("ben");
    await input.trigger("input");

    await new Promise((r) => setTimeout(r, 250));
    await flushPromises();

    // Arrow down once → first item highlighted
    await input.trigger("keydown", { key: "ArrowDown" });
    let items = wrapper.findAll(".exercise-title-item");
    expect(items[0]?.classes()).toContain("is-highlighted");

    // Arrow down again → second item highlighted
    await input.trigger("keydown", { key: "ArrowDown" });
    items = wrapper.findAll(".exercise-title-item");
    expect(items[1]?.classes()).toContain("is-highlighted");

    // Enter selects the highlighted item
    await input.trigger("keydown", { key: "Enter" });
    await flushPromises();

    expect((input.element as HTMLInputElement).value).toBe("Bench Fly");
    expect(wrapper.find(".exercise-title-dropdown").exists()).toBe(false);
  });

  it("dismisses dropdown on Escape", async () => {
    getSuggestionsMock(["Bench Press"]);
    const wrapper = mountComponent();

    const input = wrapper.find('input[placeholder="e.g., Bench Press"]');
    await input.trigger("focus");
    await input.setValue("ben");
    await input.trigger("input");

    await new Promise((r) => setTimeout(r, 250));
    await flushPromises();

    expect(wrapper.find(".exercise-title-dropdown").exists()).toBe(true);

    await input.trigger("keydown", { key: "Escape" });
    await flushPromises();

    expect(wrapper.find(".exercise-title-dropdown").exists()).toBe(false);
  });

  it("does not show dropdown when API returns no suggestions", async () => {
    getSuggestionsMock([]);
    const wrapper = mountComponent();

    const input = wrapper.find('input[placeholder="e.g., Bench Press"]');
    await input.trigger("focus");
    await input.setValue("xyz");
    await input.trigger("input");

    await new Promise((r) => setTimeout(r, 250));
    await flushPromises();

    expect(wrapper.find(".exercise-title-dropdown").exists()).toBe(false);
  });

  it("does not fire API call for empty input", async () => {
    const wrapper = mountComponent();

    const input = wrapper.find('input[placeholder="e.g., Bench Press"]');
    await input.trigger("focus");
    await input.setValue("");
    await input.trigger("input");

    await new Promise((r) => setTimeout(r, 250));
    await flushPromises();

    expect(api.get).not.toHaveBeenCalledWith(
      expect.stringContaining("/exercises/autocomplete/"),
    );
  });
});

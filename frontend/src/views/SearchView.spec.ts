import { describe, it, expect, vi, beforeEach } from "vitest";
import { mount, flushPromises } from "@vue/test-utils";
import { createRouter, createMemoryHistory } from "vue-router";
import SearchView from "./SearchView.vue";
import type {
  AutocompleteResponse,
  SearchResultsResponse,
} from "@/types/lifting";

// Mock the API client
vi.mock("@/api/client", () => ({
  api: {
    get: vi.fn(),
  },
}));

import { api } from "@/api/client";

// Create a mock router
const router = createRouter({
  history: createMemoryHistory(),
  routes: [
    { path: "/search", name: "search", component: SearchView },
    {
      path: "/session/:id",
      name: "session-detail",
      component: { template: "<div/>" },
    },
  ],
});

describe("SearchView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Default mock for results with no filters
    vi.mocked(api.get).mockResolvedValue({
      data: { items: [], total: 0 },
      error: null,
    });
  });

  function mountComponent() {
    return mount(SearchView, {
      global: {
        plugins: [router],
      },
    });
  }

  it("renders heading and input", async () => {
    const wrapper = mountComponent();
    await flushPromises();

    expect(wrapper.find("h1").text()).toBe("Search");
    expect(wrapper.find('input[type="text"]').exists()).toBe(true);
  });

  it("does not show autocomplete until 3 chars typed", async () => {
    const wrapper = mountComponent();
    await flushPromises();

    const input = wrapper.find('input[type="text"]');
    await input.setValue("be");
    await flushPromises();

    // Should not have called autocomplete API
    expect(api.get).not.toHaveBeenCalledWith(
      expect.stringContaining("/search/autocomplete/")
    );
  });

  it("calls autocomplete API with 3+ chars", async () => {
    const autocompleteResponse: AutocompleteResponse = {
      items: [
        {
          type: "session",
          id: null,
          label: "Upper A",
          value: "Upper A",
        },
        {
          type: "exercise",
          id: null,
          label: "Bench Press",
          value: "Bench Press",
        },
      ],
    };

    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url.includes("/search/autocomplete/")) {
        return Promise.resolve({ data: autocompleteResponse, error: null });
      }
      return Promise.resolve({ data: { items: [], total: 0 }, error: null });
    });

    const wrapper = mountComponent();
    await flushPromises();

    const input = wrapper.find('input[type="text"]');
    await input.setValue("ben");

    // Wait for debounce
    await new Promise((r) => setTimeout(r, 350));
    await flushPromises();

    expect(api.get).toHaveBeenCalledWith(
      expect.stringContaining("/search/autocomplete/?q=ben")
    );
  });

  it("shows autocomplete items with type prefixes", async () => {
    const autocompleteResponse: AutocompleteResponse = {
      items: [
        {
          type: "session",
          id: null,
          label: "Upper A",
          value: "Upper A",
        },
        {
          type: "exercise",
          id: null,
          label: "Bench Press",
          value: "Bench Press",
        },
      ],
    };

    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url.includes("/search/autocomplete/")) {
        return Promise.resolve({ data: autocompleteResponse, error: null });
      }
      return Promise.resolve({ data: { items: [], total: 0 }, error: null });
    });

    const wrapper = mountComponent();
    await flushPromises();

    const input = wrapper.find('input[type="text"]');
    await input.setValue("ben");

    await new Promise((r) => setTimeout(r, 350));
    await flushPromises();

    const autocompleteItems = wrapper.findAll(".autocomplete-item");
    expect(autocompleteItems.length).toBe(2);
    expect(autocompleteItems[0]?.text()).toContain("Session:");
    expect(autocompleteItems[1]?.text()).toContain("Exercise:");
  });

  it("adds filter pill on selection and clears input", async () => {
    const autocompleteResponse: AutocompleteResponse = {
      items: [
        {
          type: "session",
          id: null,
          label: "Upper A",
          value: "Upper A",
        },
      ],
    };

    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url.includes("/search/autocomplete/")) {
        return Promise.resolve({ data: autocompleteResponse, error: null });
      }
      return Promise.resolve({ data: { items: [], total: 0 }, error: null });
    });

    const wrapper = mountComponent();
    await flushPromises();

    const input = wrapper.find('input[type="text"]');
    await input.setValue("Upper");

    await new Promise((r) => setTimeout(r, 350));
    await flushPromises();

    // Click on autocomplete item
    const autocompleteItem = wrapper.find(".autocomplete-item");
    await autocompleteItem.trigger("click");
    await flushPromises();

    // Pill should appear
    const pills = wrapper.findAll(".tag");
    expect(pills.length).toBe(1);
    expect(pills[0]?.text()).toContain("Upper A");

    // Input should be cleared
    expect((input.element as HTMLInputElement).value).toBe("");
  });

  it("removes filter when pill delete is clicked", async () => {
    const autocompleteResponse: AutocompleteResponse = {
      items: [
        {
          type: "session",
          id: null,
          label: "Upper A",
          value: "Upper A",
        },
      ],
    };

    vi.mocked(api.get).mockImplementation((url: string) => {
      if (url.includes("/search/autocomplete/")) {
        return Promise.resolve({ data: autocompleteResponse, error: null });
      }
      return Promise.resolve({ data: { items: [], total: 0 }, error: null });
    });

    const wrapper = mountComponent();
    await flushPromises();

    const input = wrapper.find('input[type="text"]');
    await input.setValue("Upper");

    await new Promise((r) => setTimeout(r, 350));
    await flushPromises();

    await wrapper.find(".autocomplete-item").trigger("click");
    await flushPromises();

    // Verify pill exists
    expect(wrapper.findAll(".tag").length).toBe(1);

    // Click delete button on pill
    await wrapper.find(".tag .delete").trigger("click");
    await flushPromises();

    // Pill should be removed
    expect(wrapper.findAll(".tag").length).toBe(0);
  });

  it("displays search results correctly", async () => {
    const resultsResponse: SearchResultsResponse = {
      items: [
        {
          exercise_id: 1,
          exercise_title: "Bench Press",
          sets: [
            { weight: 135, reps: 10 },
            { weight: 135, reps: 10 },
            { weight: 135, reps: 8 },
          ],
          rest_seconds: 90,
          session_id: 1,
          session_date: "2024-01-15",
          session_title: "Upper A",
        },
      ],
      total: 1,
    };

    vi.mocked(api.get).mockResolvedValue({ data: resultsResponse, error: null });

    const wrapper = mountComponent();
    await flushPromises();

    // Check that results table shows data
    const rows = wrapper.findAll("tbody tr");
    expect(rows.length).toBe(1);

    const row = rows[0];
    if (row) {
      const cells = row.findAll("td");
      expect(cells[0]?.text()).toContain("2024-01-15");
      expect(cells[1]?.text()).toBe("Bench Press");
      expect(cells[2]?.text()).toBe("135 lbs"); // Max weight
    }
  });

  it("displays bodyweight when all sets have null weight", async () => {
    const resultsResponse: SearchResultsResponse = {
      items: [
        {
          exercise_id: 1,
          exercise_title: "Pull-ups",
          sets: [
            { weight: null, reps: 10 },
            { weight: null, reps: 8 },
            { weight: null, reps: 6 },
          ],
          rest_seconds: 120,
          session_id: 1,
          session_date: "2024-01-15",
          session_title: "Upper A",
        },
      ],
      total: 1,
    };

    vi.mocked(api.get).mockResolvedValue({ data: resultsResponse, error: null });

    const wrapper = mountComponent();
    await flushPromises();

    const rows = wrapper.findAll("tbody tr");
    const row = rows[0];
    if (row) {
      const cells = row.findAll("td");
      expect(cells[2]?.text()).toBe("bodyweight");
    }
  });

  it("displays max weight when sets have mixed weights", async () => {
    const resultsResponse: SearchResultsResponse = {
      items: [
        {
          exercise_id: 1,
          exercise_title: "Assisted Pull-ups",
          sets: [
            { weight: 50, reps: 10 },
            { weight: 60, reps: 8 },
            { weight: 40, reps: 6 },
          ],
          rest_seconds: 120,
          session_id: 1,
          session_date: "2024-01-15",
          session_title: "Upper A",
        },
      ],
      total: 1,
    };

    vi.mocked(api.get).mockResolvedValue({ data: resultsResponse, error: null });

    const wrapper = mountComponent();
    await flushPromises();

    const rows = wrapper.findAll("tbody tr");
    const row = rows[0];
    if (row) {
      const cells = row.findAll("td");
      expect(cells[2]?.text()).toBe("60 lbs"); // Max weight
    }
  });
});

import { describe, it, expect, vi } from "vitest";
import { mount, flushPromises } from "@vue/test-utils";
import { defineComponent, ref } from "vue";
import Autocomplete from "./Autocomplete.vue";

const suggestions = [
  { title: "Lat raises", count: 11, last_date: "2026-01-21" },
  { title: "Lat raise (cable)", count: 2, last_date: "2025-10-16" },
];

// The way PlanView uses it: v-model plus a commit handler that stores what was typed.
function mountWithParent() {
  const committed: string[] = [];
  const Parent = defineComponent({
    components: { Autocomplete },
    setup() {
      const title = ref("");
      const fetch = () => Promise.resolve(suggestions);
      const onCommit = (v: string) => {
        committed.push(v);
        title.value = v;
      };
      return { title, fetch, onCommit };
    },
    template: `<Autocomplete v-model="title" :fetch="fetch" label="Exercise name" @commit="onCommit" />`,
  });
  const wrapper = mount(Parent, { attachTo: document.body });
  return { wrapper, committed };
}

describe("Autocomplete", () => {
  it("picking a suggestion fills the input and isn't overwritten by what was typed", async () => {
    vi.useFakeTimers();
    const { wrapper, committed } = mountWithParent();
    const input = wrapper.find("input");
    (input.element as HTMLInputElement).focus(); // really focused, so the component's blur() fires blur
    await input.setValue("Lat r");
    vi.advanceTimersByTime(200);
    vi.useRealTimers();
    await flushPromises();

    await wrapper.findAll(".ac-item")[0]!.trigger("mousedown");
    await flushPromises();

    expect((input.element as HTMLInputElement).value).toBe("Lat raises");
    expect(committed).not.toContain("Lat r");
    wrapper.unmount();
  });

  it("commits typed text on blur when nothing was picked", async () => {
    const { wrapper, committed } = mountWithParent();
    const input = wrapper.find("input");
    await input.trigger("focus");
    await input.setValue("Face pulls");
    await input.trigger("blur");
    expect(committed).toEqual(["Face pulls"]);
    wrapper.unmount();
  });
});

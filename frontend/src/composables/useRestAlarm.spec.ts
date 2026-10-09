import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { defineComponent, h } from "vue";
import { mount } from "@vue/test-utils";
import { createPinia, setActivePinia } from "pinia";
import { useActiveSessionStore } from "@/stores/activeSession";
import { useRestAlarm } from "./useRestAlarm";

vi.mock("@/utils/audio", () => ({ playAlarm: vi.fn(), vibrate: vi.fn(), unlockAudio: vi.fn() }));
vi.mock("@/api/client", () => ({ api: {} }));

import { playAlarm, vibrate } from "@/utils/audio";

function host(enabled = () => true) {
  return mount(
    defineComponent({
      setup() {
        useRestAlarm(enabled);
        return () => h("div");
      },
    }),
  );
}

describe("useRestAlarm", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.clearAllMocks();
    setActivePinia(createPinia());
    const store = useActiveSessionStore();
    store.session = { id: 1, title: "", date: "", comments: "", status: "active", started_at: null, finished_at: null, exercises: [] };
  });
  afterEach(() => vi.useRealTimers());

  it("sounds once when rest hits zero, with no rest screen showing", async () => {
    const wrapper = host();
    useActiveSessionStore().startRest(2);
    await vi.advanceTimersByTimeAsync(1500);
    expect(playAlarm).not.toHaveBeenCalled();
    await vi.advanceTimersByTimeAsync(1000);
    expect(playAlarm).toHaveBeenCalledTimes(1);
    expect(vibrate).toHaveBeenCalledTimes(1);
    await vi.advanceTimersByTimeAsync(2000);
    expect(playAlarm).toHaveBeenCalledTimes(1);
    wrapper.unmount();
  });

  it("stays quiet when disabled or paused", async () => {
    const store = useActiveSessionStore();
    const wrapper = host(() => false);
    store.startRest(1);
    await vi.advanceTimersByTimeAsync(2000);
    wrapper.unmount();
    const live = host();
    store.startRest(1);
    store.toggleRestPause();
    await vi.advanceTimersByTimeAsync(2000);
    expect(playAlarm).not.toHaveBeenCalled();
    live.unmount();
  });
});

import { describe, it, expect, beforeEach, vi } from "vitest";
import { setActivePinia, createPinia } from "pinia";
import { useActiveSessionStore } from "./activeSession";
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

import { api } from "@/api/client";

function exercise(id: number, title: string, done: boolean[], group: number | null = null, rest = 90): Exercise {
  return {
    id,
    title,
    sets: done.map((d) => ({ weight: 100, reps: 5, done: d })),
    rest_seconds: rest,
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

async function loaded(exercises: Exercise[]) {
  vi.mocked(api.get).mockResolvedValue({ data: session(exercises), error: null });
  const store = useActiveSessionStore();
  await store.load(1);
  return store;
}

describe("activeSession store", () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    vi.clearAllMocks();
    const memory = new Map<string, string>();
    vi.stubGlobal("localStorage", {
      getItem: (k: string) => memory.get(k) ?? null,
      setItem: (k: string, v: string) => memory.set(k, v),
      removeItem: (k: string) => memory.delete(k),
    });
    vi.mocked(api.put).mockResolvedValue({ data: {}, error: null });
  });

  describe("current unit", () => {
    it("is the first set not done", async () => {
      const store = await loaded([exercise(1, "Bench", [true, true]), exercise(2, "Pull-ups", [true, false, false])]);
      expect(store.position).toEqual({ unitIndex: 1, round: 1, exerciseIndex: 1 });
    });

    it("walks a superset round by round, A then B", async () => {
      const store = await loaded([
        exercise(1, "Bench", [true]),
        exercise(2, "Flyes", [true, true, false], 1),
        exercise(3, "Lat raises", [true, false, false], 1),
      ]);
      expect(store.currentUnit?.isSuperset).toBe(true);
      expect(store.position).toEqual({ unitIndex: 1, round: 1, exerciseIndex: 2 });
    });

    it("follows a jump, then returns to the first undone set when that unit is done", async () => {
      const store = await loaded([exercise(1, "Bench", [false]), exercise(2, "Curl", [false])]);
      store.jumpTo(1);
      expect(store.position?.exerciseIndex).toBe(1);
      await store.logSet(1, 0, { weight: 30, reps: 10 });
      expect(store.position?.exerciseIndex).toBe(0);
    });

    it("is null when everything is done", async () => {
      const store = await loaded([exercise(1, "Bench", [true, true])]);
      expect(store.position).toBeNull();
      expect(store.isComplete).toBe(true);
    });
  });

  describe("logSet", () => {
    it("replaces the target with what was lifted and saves the full sets array", async () => {
      const store = await loaded([exercise(7, "Bench", [true, false])]);
      const ok = await store.logSet(0, 1, { weight: 152.5, reps: 4 });
      expect(ok).toBe(true);
      expect(api.put).toHaveBeenCalledWith("/api/lifting/exercises/7/", {
        sets: [
          { weight: 100, reps: 5, done: true },
          { weight: 152.5, reps: 4, done: true },
        ],
      });
      expect(store.exercises[0]!.sets[1]).toEqual({ weight: 152.5, reps: 4, done: true });
    });

    it("rolls back done on error but keeps the numbers, and retry saves them", async () => {
      const store = await loaded([exercise(7, "Bench", [false])]);
      vi.mocked(api.put).mockResolvedValueOnce({ data: null, error: "Request failed" });
      const ok = await store.logSet(0, 0, { weight: 155, reps: 3 });
      expect(ok).toBe(false);
      expect(store.exercises[0]!.sets[0]).toEqual({ weight: 155, reps: 3, done: false });
      expect(store.saveError).toBeTruthy();
      expect(store.unsaved).toHaveLength(1);

      await store.retry();
      expect(store.exercises[0]!.sets[0]!.done).toBe(true);
      expect(store.unsaved).toHaveLength(0);
      expect(store.saveError).toBeNull();
    });
  });

  it("editSet corrects a done set without undoing it", async () => {
    const store = await loaded([exercise(7, "Bench", [true])]);
    await store.editSet(0, 0, { weight: 95, reps: 5 });
    expect(store.exercises[0]!.sets[0]).toEqual({ weight: 95, reps: 5, done: true });
  });

  describe("rest", () => {
    it("tracks an end time, survives a reload, and adjusts", async () => {
      vi.useFakeTimers();
      vi.setSystemTime(new Date(2026, 0, 23, 8, 0, 0));
      const store = await loaded([exercise(1, "Bench", [false])]);
      store.startRest(240, "Bench");
      vi.advanceTimersByTime(60_000);
      expect(store.remaining()).toBe(180);
      store.adjustRest(-15);
      expect(store.remaining()).toBe(165);

      setActivePinia(createPinia());
      const reloaded = await loaded([exercise(1, "Bench", [false])]);
      expect(reloaded.rest?.label).toBe("Bench");
      expect(reloaded.remaining()).toBe(165);

      reloaded.toggleRestPause();
      vi.advanceTimersByTime(30_000);
      expect(reloaded.remaining()).toBe(165);
      reloaded.toggleRestPause();
      vi.advanceTimersByTime(5_000);
      expect(reloaded.remaining()).toBe(160);
      vi.useRealTimers();
    });
  });

  it("finish posts comments and clears the session", async () => {
    const store = await loaded([exercise(1, "Bench", [true, false])]);
    const finished = { ...session([exercise(1, "Bench", [true])]), status: "done" };
    vi.mocked(api.post).mockResolvedValue({ data: finished, error: null });
    store.startRest(60);
    const result = await store.finish("Good one");
    expect(api.post).toHaveBeenCalledWith("/api/lifting/sessions/1/finish/", { comments: "Good one" });
    expect(result?.exercises[0]!.sets).toHaveLength(1);
    expect(store.session).toBeNull();
    expect(store.rest).toBeNull();
  });

  it("adds a superset partner with the upcoming exercise, matching its rounds", async () => {
    const store = await loaded([exercise(1, "Bench", [false]), exercise(2, "Leg raises", [false, false, false], null, 120)]);
    vi.mocked(api.post).mockResolvedValue({ data: {}, error: null });
    await store.addExercise({ title: "Face pulls", sets: [{ weight: 40, reps: 15 }], rest_seconds: 60 }, "superset");
    expect(api.put).toHaveBeenCalledWith("/api/lifting/exercises/2/", { superset_group: 1 });
    expect(api.post).toHaveBeenCalledWith("/api/lifting/sessions/1/exercises/", {
      title: "Face pulls",
      sets: Array(3).fill({ weight: 40, reps: 15, done: false }),
      rest_seconds: 120,
      comments: "",
      superset_group: 1,
      position: 3,
    });
  });

  describe("session note", () => {
    it("saves once after typing stops", async () => {
      vi.useFakeTimers();
      const store = await loaded([exercise(1, "Bench", [false])]);
      store.saveSessionNote("Shoulder's");
      store.saveSessionNote("Shoulder's cranky");
      expect(store.session?.comments).toBe("Shoulder's cranky");
      await vi.advanceTimersByTimeAsync(700);
      expect(api.put).toHaveBeenCalledTimes(1);
      expect(api.put).toHaveBeenCalledWith("/api/lifting/sessions/1/", { comments: "Shoulder's cranky" });
      vi.useRealTimers();
    });

    it("flushNotes sends a pending note right away, once", async () => {
      vi.useFakeTimers();
      const store = await loaded([exercise(1, "Bench", [false])]);
      store.saveSessionNote("Cranky");
      await store.flushNotes();
      expect(api.put).toHaveBeenCalledWith("/api/lifting/sessions/1/", { comments: "Cranky" });
      await vi.advanceTimersByTimeAsync(1000);
      expect(api.put).toHaveBeenCalledTimes(1);
      vi.useRealTimers();
    });
  });

  it("settle waits for queued saves and sends pending notes", async () => {
    const store = await loaded([exercise(1, "Bench", [false, false])]);
    let release: (value: { data: object; error: null }) => void = () => {};
    vi.mocked(api.put).mockImplementationOnce(() => new Promise((resolve) => (release = resolve)));
    store.logSet(0, 0, { weight: 100, reps: 5 });
    store.saveNote(0, "Felt fast");
    store.saveSessionNote("Good day");
    let settled = false;
    const settling = store.settle().then(() => (settled = true));
    await new Promise((r) => setTimeout(r));
    expect(settled).toBe(false);
    release({ data: {}, error: null });
    await settling;
    expect(api.put).toHaveBeenCalledWith("/api/lifting/exercises/1/", { comments: "Felt fast" });
    expect(api.put).toHaveBeenCalledWith("/api/lifting/sessions/1/", { comments: "Good day" });
  });
});

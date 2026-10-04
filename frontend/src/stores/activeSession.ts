import { defineStore } from "pinia";
import { ref, computed } from "vue";
import { api } from "@/api/client";
import type { Exercise, Session, Set, SetValues } from "@/types/lifting";
import { groupUnits, positionInUnit, currentPosition, roundCount, type Position } from "@/utils/session";
import { MAX_SETS } from "@/utils/plan";

export interface RestState {
  sessionId: number;
  /** Epoch ms when rest ends, so a backgrounded or reloaded PWA shows the right time. */
  endAt: number;
  total: number; // seconds, for "of 4:00" and the progress bar
  pausedRemaining: number | null; // seconds left while paused
  label: string; // what the rest follows, e.g. "Bench"
}

export type Placement = "next" | "end" | "superset";

const REST_KEY = "coach.rest";
const NOTE_DEBOUNCE_MS = 700;

function readStoredRest(): RestState | null {
  try {
    const raw = localStorage.getItem(REST_KEY);
    return raw ? (JSON.parse(raw) as RestState) : null;
  } catch {
    return null;
  }
}

function storeRest(rest: RestState | null) {
  try {
    if (rest) localStorage.setItem(REST_KEY, JSON.stringify(rest));
    else localStorage.removeItem(REST_KEY);
  } catch {
    // Without storage the timer still works; it just won't survive a reload.
  }
}

export const useActiveSessionStore = defineStore("activeSession", () => {
  const session = ref<Session | null>(null);
  const loading = ref(false);
  const error = ref<string | null>(null);
  /** Sets that were logged but didn't save: shown in a retry banner, values kept. */
  const unsaved = ref<{ exerciseId: number; setIndex: number; values: SetValues }[]>([]);
  const saveError = ref<string | null>(null);
  /** Unit the lifter jumped to from the progress strip; null follows the first undone set. */
  const focusUnit = ref<number | null>(null);
  const rest = ref<RestState | null>(null);

  const exercises = computed(() => session.value?.exercises ?? []);
  const units = computed(() => groupUnits(exercises.value));

  const position = computed((): Position | null => {
    const focused = focusUnit.value !== null ? units.value[focusUnit.value] : undefined;
    if (focused) {
      const inFocus = positionInUnit(focused, focusUnit.value!);
      if (inFocus) return inFocus;
    }
    return currentPosition(exercises.value);
  });

  const currentUnit = computed(() => (position.value ? units.value[position.value.unitIndex]! : null));
  const isComplete = computed(() => exercises.value.length > 0 && position.value === null);
  const doneSetCount = computed(() => exercises.value.reduce((n, e) => n + e.sets.filter((s) => s.done).length, 0));

  // ---------- Loading ----------

  async function load(id: number): Promise<Session | null> {
    if (session.value?.id !== id) {
      session.value = null;
      focusUnit.value = null;
      unsaved.value = [];
    }
    loading.value = true;
    error.value = null;
    const response = await api.get<Session>(`/api/lifting/sessions/${id}/`);
    loading.value = false;
    if (!response.data) {
      error.value = response.error || "Couldn't load the session";
      return null;
    }
    session.value = response.data;
    const stored = readStoredRest();
    rest.value = stored && stored.sessionId === id ? stored : null;
    return response.data;
  }

  // ---------- Saving sets ----------

  // One request at a time per exercise, each sending the latest sets, so saves can't land out of order.
  const queues = new Map<number, Promise<boolean>>();

  function saveExercise(exercise: Exercise, fields: Partial<Pick<Exercise, "sets" | "comments" | "superset_group">>) {
    const previous = queues.get(exercise.id) ?? Promise.resolve(true);
    const next = previous.then(async () => {
      const body = "sets" in fields ? { ...fields, sets: exercise.sets } : fields;
      const response = await api.put<Exercise>(`/api/lifting/exercises/${exercise.id}/`, body);
      return response.data !== null;
    });
    queues.set(exercise.id, next);
    return next;
  }

  /**
   * Log a set: what was lifted replaces the target and it's marked done, then
   * it's saved. If the save fails the set goes back to not done, keeping the
   * numbers, and appears in the retry banner.
   */
  async function logSet(exerciseIndex: number, setIndex: number, values: SetValues): Promise<boolean> {
    const exercise = exercises.value[exerciseIndex];
    const set = exercise?.sets[setIndex];
    if (!exercise || !set) return false;
    Object.assign(set, values, { done: true });
    unsaved.value = unsaved.value.filter((u) => !(u.exerciseId === exercise.id && u.setIndex === setIndex));

    await api.fetchCsrfToken();
    const ok = await saveExercise(exercise, { sets: exercise.sets });
    if (!ok) {
      set.done = false;
      unsaved.value.push({ exerciseId: exercise.id, setIndex, values: { ...values } });
      saveError.value = "Couldn't save. Check your connection.";
    } else if (unsaved.value.length === 0) {
      saveError.value = null;
    }
    return ok;
  }

  /** Re-send every set that failed to save. */
  async function retry(): Promise<void> {
    const pending = unsaved.value;
    unsaved.value = [];
    saveError.value = null;
    for (const item of pending) {
      const index = exercises.value.findIndex((e) => e.id === item.exerciseId);
      if (index >= 0) await logSet(index, item.setIndex, item.values);
    }
  }

  /** Correct a set (done or not) without changing whether it's done. */
  async function editSet(exerciseIndex: number, setIndex: number, values: SetValues): Promise<boolean> {
    const exercise = exercises.value[exerciseIndex];
    const set = exercise?.sets[setIndex];
    if (!exercise || !set) return false;
    Object.assign(set, values);
    await api.fetchCsrfToken();
    const ok = await saveExercise(exercise, { sets: exercise.sets });
    if (!ok) saveError.value = "Couldn't save that change. Check your connection.";
    return ok;
  }

  /** Add one more set to the current unit (copying the last), e.g. a bonus set. */
  async function addSet(exerciseIndex: number): Promise<void> {
    const unit = units.value.find((u) => exerciseIndex >= u.start && exerciseIndex < u.start + u.items.length);
    if (!unit || roundCount(unit) >= MAX_SETS) return;
    await api.fetchCsrfToken();
    await Promise.all(
      unit.items.map((exercise) => {
        const last = exercise.sets[exercise.sets.length - 1];
        exercise.sets.push({ weight: last?.weight ?? null, reps: last?.reps ?? 0, done: false });
        return saveExercise(exercise, { sets: exercise.sets });
      }),
    );
  }

  // ---------- Notes ----------

  const noteTimers = new Map<number, ReturnType<typeof setTimeout>>();

  function saveNote(exerciseIndex: number, text: string) {
    const exercise = exercises.value[exerciseIndex];
    if (!exercise) return;
    exercise.comments = text;
    const existing = noteTimers.get(exercise.id);
    if (existing) clearTimeout(existing);
    noteTimers.set(
      exercise.id,
      setTimeout(async () => {
        noteTimers.delete(exercise.id);
        await api.fetchCsrfToken();
        if (!(await saveExercise(exercise, { comments: exercise.comments }))) {
          saveError.value = "Couldn't save the note. Check your connection.";
        }
      }, NOTE_DEBOUNCE_MS),
    );
  }

  /** Send any note still waiting on its debounce. */
  async function flushNotes() {
    const pending = Array.from(noteTimers.entries());
    noteTimers.clear();
    await Promise.all(
      pending.map(([id, timer]) => {
        clearTimeout(timer);
        const exercise = exercises.value.find((e) => e.id === id);
        return exercise ? saveExercise(exercise, { comments: exercise.comments }) : true;
      }),
    );
  }

  // ---------- Structure ----------

  /** The unit after the current one: what a new exercise can be supersetted with. */
  const upcomingUnit = computed(() => {
    const index = position.value ? position.value.unitIndex + 1 : -1;
    return index > 0 ? (units.value[index] ?? null) : null;
  });

  async function addExercise(input: { title: string; sets: SetValues[]; rest_seconds: number }, placement: Placement) {
    const current = session.value;
    if (!current) return false;
    await api.fetchCsrfToken();

    let position: number | undefined;
    let group: number | null = null;
    let sets: Set[] = input.sets.slice(0, MAX_SETS).map((s) => ({ ...s, done: false }));
    let rest = input.rest_seconds;

    if (placement === "next" && currentUnit.value) {
      position = currentUnit.value.items[currentUnit.value.items.length - 1]!.position + 1;
    } else if (placement === "superset" && upcomingUnit.value) {
      const target = upcomingUnit.value;
      const lastMember = target.items[target.items.length - 1]!;
      position = lastMember.position + 1;
      group = target.items[0]!.superset_group;
      rest = target.items[0]!.rest_seconds;
      if (group === null) {
        group = Math.max(0, ...exercises.value.map((e) => e.superset_group ?? 0)) + 1;
        if (!(await saveExercise(target.items[0]!, { superset_group: group }))) return false;
      }
      // Supersets have equal set counts
      const rounds = roundCount(target);
      while (sets.length < rounds) sets.push({ ...(sets[sets.length - 1] ?? { weight: null, reps: 0 }), done: false });
      sets = sets.slice(0, rounds);
    }

    const response = await api.post<Exercise>(`/api/lifting/sessions/${current.id}/exercises/`, {
      title: input.title,
      sets,
      rest_seconds: rest,
      comments: "",
      superset_group: group,
      ...(position !== undefined ? { position } : {}),
    });
    if (!response.data) {
      saveError.value = response.error || "Couldn't add the exercise";
      return false;
    }
    await load(current.id);
    return true;
  }

  function jumpTo(unitIndex: number) {
    focusUnit.value = unitIndex;
  }

  // ---------- Rest ----------

  function remaining(now = Date.now()): number {
    const r = rest.value;
    if (!r) return 0;
    if (r.pausedRemaining !== null) return r.pausedRemaining;
    return Math.max(0, (r.endAt - now) / 1000);
  }

  function setRest(next: RestState | null) {
    rest.value = next;
    storeRest(next);
  }

  function startRest(seconds: number, label = rest.value?.label ?? "") {
    if (!session.value || seconds <= 0) return setRest(null);
    setRest({ sessionId: session.value.id, endAt: Date.now() + seconds * 1000, total: seconds, pausedRemaining: null, label });
  }

  function adjustRest(deltaSeconds: number) {
    const r = rest.value;
    if (!r) return;
    if (r.pausedRemaining !== null) {
      setRest({ ...r, pausedRemaining: Math.max(0, r.pausedRemaining + deltaSeconds) });
    } else {
      setRest({ ...r, endAt: Math.max(Date.now(), r.endAt + deltaSeconds * 1000) });
    }
  }

  function toggleRestPause() {
    const r = rest.value;
    if (!r) return;
    if (r.pausedRemaining === null) setRest({ ...r, pausedRemaining: remaining() });
    else setRest({ ...r, endAt: Date.now() + r.pausedRemaining * 1000, pausedRemaining: null });
  }

  function endRest() {
    setRest(null);
  }

  // ---------- Finishing ----------

  async function finish(comments: string): Promise<Session | null> {
    if (!session.value) return null;
    await flushNotes();
    await api.fetchCsrfToken();
    const response = await api.post<Session>(`/api/lifting/sessions/${session.value.id}/finish/`, { comments });
    if (!response.data) {
      saveError.value = response.error || "Couldn't finish the session";
      return null;
    }
    endRest();
    session.value = null;
    focusUnit.value = null;
    return response.data;
  }

  return {
    session,
    loading,
    error,
    unsaved,
    saveError,
    focusUnit,
    rest,
    exercises,
    units,
    position,
    currentUnit,
    upcomingUnit,
    isComplete,
    doneSetCount,
    load,
    logSet,
    retry,
    editSet,
    addSet,
    saveNote,
    flushNotes,
    addExercise,
    jumpTo,
    remaining,
    startRest,
    adjustRest,
    toggleRestPause,
    endRest,
    finish,
  };
});

import type { Exercise, ExercisePayload, Set } from "@/types/lifting";
import { groupUnits } from "@/utils/session";

/** No exercise goes past six sets; the set-chip grid assumes it. */
export const MAX_SETS = 6;
export const DEFAULT_REST = 90;

export interface DraftSet {
  weight: number | null;
  reps: number;
}

export interface DraftExercise {
  key: number; // stable identity for rendering
  id?: number; // set when the exercise already exists on the server
  title: string;
  /** The committed name whose history is shown (title changes on every keystroke). */
  historyTitle: string;
  sets: DraftSet[];
  rest_seconds: number;
  comments: string;
  superset_group: number | null;
}

let lastKey = 0;
function nextKey(): number {
  return ++lastKey;
}

export function blankSet(): DraftSet {
  return { weight: null, reps: 0 };
}

export function blankExercise(): DraftExercise {
  return {
    key: nextKey(),
    title: "",
    historyTitle: "",
    sets: [blankSet()],
    rest_seconds: DEFAULT_REST,
    comments: "",
    superset_group: null,
  };
}

/** A set is blank until it has reps; a brand new exercise has exactly one. */
export function hasOnlyBlankSets(exercise: DraftExercise): boolean {
  return exercise.sets.every((s) => s.reps === 0 && s.weight === null);
}

export function copySets(sets: { weight: number | null; reps: number }[]): DraftSet[] {
  return sets.slice(0, MAX_SETS).map((s) => ({ weight: s.weight, reps: s.reps }));
}

/**
 * Draft from a saved exercise. With keepIds the draft edits that exercise;
 * without, it's a copy (Start from) and comments are left behind.
 */
export function draftFromExercise(exercise: Exercise, keepIds: boolean): DraftExercise {
  return {
    key: nextKey(),
    id: keepIds ? exercise.id : undefined,
    title: exercise.title,
    historyTitle: exercise.title,
    sets: copySets(exercise.sets),
    rest_seconds: exercise.rest_seconds,
    comments: keepIds ? exercise.comments : "",
    superset_group: exercise.superset_group,
  };
}

/** Index range [start, end) of the unit (single exercise or superset) containing index. */
export function unitRange(exercises: DraftExercise[], index: number): [number, number] {
  const unit = groupUnits(exercises).find((u) => index >= u.start && index < u.start + u.items.length);
  return unit ? [unit.start, unit.start + unit.items.length] : [index, index + 1];
}

function members(exercises: DraftExercise[], index: number): DraftExercise[] {
  const [start, end] = unitRange(exercises, index);
  return exercises.slice(start, end);
}

/** Pad (copying the last set) or trim one exercise's sets to count. */
export function resizeSets(exercise: DraftExercise, count: number) {
  while (exercise.sets.length < count) {
    const last = exercise.sets[exercise.sets.length - 1];
    exercise.sets.push(last ? { ...last } : blankSet());
  }
  exercise.sets.length = count;
}

/** Change the set count (rounds, for a superset: every member changes). New sets copy the last. */
export function setSetCount(exercises: DraftExercise[], index: number, count: number) {
  const clamped = Math.min(MAX_SETS, Math.max(1, count));
  members(exercises, index).forEach((e) => resizeSets(e, clamped));
}

export function copyFirstSetToAll(exercise: DraftExercise) {
  const first = exercise.sets[0];
  if (!first) return;
  exercise.sets = exercise.sets.map(() => ({ ...first }));
}

/** Renumber superset groups 1..n in order and dissolve any group left with one member. */
export function normalizeGroups(exercises: DraftExercise[]) {
  let next = 0;
  for (const unit of groupUnits(exercises)) {
    if (unit.items.length < 2) {
      unit.items.forEach((e) => (e.superset_group = null));
    } else {
      next++;
      unit.items.forEach((e) => (e.superset_group = next));
    }
  }
}

export function canLinkWithNext(exercises: DraftExercise[], index: number): boolean {
  const [, end] = unitRange(exercises, index);
  return end < exercises.length && end - 1 === index;
}

/**
 * Link the exercise's unit with the unit below it. Members share the first
 * exercise's rest and are padded to the same set count.
 */
export function linkWithNext(exercises: DraftExercise[], index: number) {
  if (!canLinkWithNext(exercises, index)) return;
  const [start] = unitRange(exercises, index);
  const [, end] = unitRange(exercises, index + 1);
  const group = exercises.slice(start, end);
  const marker = -1; // temporary; normalizeGroups assigns the real number
  const rounds = Math.max(...group.map((e) => e.sets.length));
  const rest = group[0]!.rest_seconds;
  group.forEach((e) => {
    e.superset_group = marker;
    e.rest_seconds = rest;
    resizeSets(e, rounds);
  });
  normalizeGroups(exercises);
}

/** Dissolve the superset containing index. */
export function unlink(exercises: DraftExercise[], index: number) {
  members(exercises, index).forEach((e) => (e.superset_group = null));
  normalizeGroups(exercises);
}

export function removeExercise(exercises: DraftExercise[], index: number) {
  exercises.splice(index, 1);
  normalizeGroups(exercises);
}

export function canMove(exercises: DraftExercise[], index: number, direction: -1 | 1): boolean {
  const [start, end] = unitRange(exercises, index);
  const insideUnit = direction < 0 ? index > start : index < end - 1;
  if (insideUnit) return true;
  return direction < 0 ? start > 0 : end < exercises.length;
}

/**
 * Move an exercise up or down. Inside a superset this swaps members; at a
 * superset's edge the whole superset moves past its neighbour.
 */
export function move(exercises: DraftExercise[], index: number, direction: -1 | 1) {
  if (!canMove(exercises, index, direction)) return;
  const [start, end] = unitRange(exercises, index);
  const insideUnit = direction < 0 ? index > start : index < end - 1;
  if (insideUnit) {
    const other = index + direction;
    [exercises[index], exercises[other]] = [exercises[other]!, exercises[index]!];
    // The group's rest belongs to whichever member is first
    const rest = exercises[start]!.rest_seconds;
    exercises.slice(start, end).forEach((e) => (e.rest_seconds = rest));
    return;
  }
  const unit = exercises.splice(start, end - start);
  if (direction < 0) {
    const [prevStart] = unitRange(exercises, start - 1);
    exercises.splice(prevStart, 0, ...unit);
  } else {
    const [, nextEnd] = unitRange(exercises, start);
    exercises.splice(nextEnd, 0, ...unit);
  }
}

/** Rest applies to every member of a superset. */
export function setRest(exercises: DraftExercise[], index: number, seconds: number) {
  members(exercises, index).forEach((e) => (e.rest_seconds = seconds));
}

export interface PlanForm {
  title: string;
  date: string;
  exercises: DraftExercise[];
}

/** Errors keyed "title", "date", "exercises", "exercise.<key>.title", "exercise.<key>.sets". */
export function validatePlan(form: PlanForm, opts: { allowFuture: boolean; today: string }): Record<string, string> {
  const errors: Record<string, string> = {};
  if (!form.title.trim()) errors.title = "Give it a title";
  if (!form.date) errors.date = "Pick a date";
  else if (!opts.allowFuture && form.date > opts.today) errors.date = "Can't be in the future";
  if (form.exercises.length === 0) errors.exercises = "Add at least one exercise";
  for (const e of form.exercises) {
    if (!e.title.trim()) errors[`exercise.${e.key}.title`] = "Name this exercise";
    if (e.sets.length === 0 || e.sets.some((s) => s.reps < 1)) errors[`exercise.${e.key}.sets`] = "Every set needs reps";
  }
  return errors;
}

/** Plans hold targets (done: false); a finished session being edited holds actuals (done: true). */
export function toPayload(exercises: DraftExercise[], done: boolean): ExercisePayload[] {
  return exercises.map((e) => ({
    ...(e.id ? { id: e.id } : {}),
    title: e.title.trim(),
    sets: e.sets.map((s): Set => ({ weight: s.weight, reps: s.reps, done })),
    rest_seconds: e.rest_seconds,
    comments: e.comments.trim(),
    superset_group: e.superset_group,
  }));
}

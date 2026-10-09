import { describe, it, expect } from "vitest";
import {
  type DraftExercise,
  blankExercise,
  setSetCount,
  copyFirstSetToAll,
  linkWithNext,
  canLinkWithNext,
  unlink,
  removeExercise,
  move,
  canMove,
  setRest,
  validatePlan,
  toPayload,
  minSetCount,
  draftFromExercise,
  MAX_SETS,
} from "./plan";

function ex(title: string, sets: [number | null, number][], rest = 90, group: number | null = null): DraftExercise {
  return {
    ...blankExercise(),
    title,
    historyTitle: title,
    sets: sets.map(([weight, reps]) => ({ weight, reps, done: false })),
    rest_seconds: rest,
    superset_group: group,
  };
}

const titles = (list: DraftExercise[]) => list.map((e) => e.title);
const groups = (list: DraftExercise[]) => list.map((e) => e.superset_group);

describe("set count", () => {
  it("adds sets by copying the last one", () => {
    const list = [ex("Bench", [[150, 5], [155, 5]])];
    setSetCount(list, 0, 4);
    expect(list[0]!.sets).toEqual([
      { weight: 150, reps: 5, done: false },
      { weight: 155, reps: 5, done: false },
      { weight: 155, reps: 5, done: false },
      { weight: 155, reps: 5, done: false },
    ]);
    list[0]!.sets[3]!.reps = 3;
    expect(list[0]!.sets[2]!.reps).toBe(5); // copies, not shared objects
  });

  it("removes from the end and clamps to 1..6", () => {
    const list = [ex("Bench", [[150, 5], [155, 5]])];
    setSetCount(list, 0, 0);
    expect(list[0]!.sets).toEqual([{ weight: 150, reps: 5, done: false }]);
    setSetCount(list, 0, 10);
    expect(list[0]!.sets).toHaveLength(MAX_SETS);
  });

  it("changes every member of a superset", () => {
    const list = [ex("A", [[20, 12]], 90, 1), ex("B", [[30, 12]], 90, 1), ex("C", [[1, 1]])];
    setSetCount(list, 1, 3);
    expect(list.map((e) => e.sets.length)).toEqual([3, 3, 1]);
  });

  it("never drops below the done sets, and new sets aren't done", () => {
    const list = [ex("Bench", [[150, 5], [155, 5], [155, 4]])];
    list[0]!.sets[0]!.done = true;
    list[0]!.sets[1]!.done = true;
    expect(minSetCount(list, 0)).toBe(2);
    setSetCount(list, 0, 1);
    expect(list[0]!.sets.map((s) => s.done)).toEqual([true, true]);
    setSetCount(list, 0, 3);
    expect(list[0]!.sets.map((s) => s.done)).toEqual([true, true, false]);
    expect(list[0]!.sets[2]).toEqual({ weight: 155, reps: 5, done: false });
  });

  it("a superset's floor is its most-done member", () => {
    const list = [ex("A", [[20, 12], [20, 12], [20, 12]], 90, 1), ex("B", [[30, 12], [30, 12], [30, 12]], 90, 1)];
    list[1]!.sets[0]!.done = true;
    list[1]!.sets[1]!.done = true;
    setSetCount(list, 0, 1);
    expect(list.map((e) => e.sets.length)).toEqual([2, 2]);
  });
});

it("copies set 1 to all", () => {
  const e = ex("Bench", [[150, 5], [155, 4], [160, 3]]);
  copyFirstSetToAll(e);
  expect(e.sets.map((s) => [s.weight, s.reps])).toEqual([[150, 5], [150, 5], [150, 5]]);
});

it("copying set 1 to all leaves done sets alone", () => {
  const e = ex("Bench", [[150, 5], [155, 4], [160, 3]]);
  e.sets[1]!.done = true;
  copyFirstSetToAll(e);
  expect(e.sets).toEqual([
    { weight: 150, reps: 5, done: false },
    { weight: 155, reps: 4, done: true },
    { weight: 150, reps: 5, done: false },
  ]);
});

it("a draft of a saved exercise keeps done flags; a copy doesn't", () => {
  const saved = { id: 3, title: "Bench", sets: [{ weight: 150, reps: 5, done: true }], rest_seconds: 90, comments: "", position: 0, superset_group: null };
  expect(draftFromExercise(saved, true).sets[0]!.done).toBe(true);
  expect(draftFromExercise(saved, false).sets[0]!.done).toBe(false);
});

describe("supersets", () => {
  it("links with the next exercise, sharing rest and evening out sets", () => {
    const list = [ex("Flyes", [[20, 12], [20, 12], [20, 12]], 60), ex("Lat raises", [[30, 12]], 120)];
    linkWithNext(list, 0);
    expect(groups(list)).toEqual([1, 1]);
    expect(list.map((e) => e.rest_seconds)).toEqual([60, 60]);
    expect(list[1]!.sets).toHaveLength(3);
  });

  it("linking pads with sets that aren't done and keeps the done ones", () => {
    const list = [ex("Flyes", [[20, 12], [20, 12]]), ex("Lat raises", [[30, 12]])];
    list[1]!.sets[0]!.done = true;
    expect(canLinkWithNext(list, 0)).toBe(true);
    linkWithNext(list, 0);
    expect(list[1]!.sets.map((s) => s.done)).toEqual([true, false]);
  });

  it("only the last member of a unit can link onward", () => {
    const list = [ex("A", [[1, 1]], 90, 1), ex("B", [[1, 1]], 90, 1), ex("C", [[1, 1]])];
    expect(canLinkWithNext(list, 0)).toBe(false);
    expect(canLinkWithNext(list, 1)).toBe(true);
    expect(canLinkWithNext(list, 2)).toBe(false);
    linkWithNext(list, 1);
    expect(groups(list)).toEqual([1, 1, 1]);
  });

  it("unlink dissolves the whole superset", () => {
    const list = [ex("A", [[1, 1]], 90, 1), ex("B", [[1, 1]], 90, 1)];
    unlink(list, 1);
    expect(groups(list)).toEqual([null, null]);
  });

  it("removing a member of a pair dissolves it, and groups renumber", () => {
    const list = [
      ex("A", [[1, 1]], 90, 1),
      ex("B", [[1, 1]], 90, 1),
      ex("C", [[1, 1]], 90, 2),
      ex("D", [[1, 1]], 90, 2),
    ];
    removeExercise(list, 0);
    expect(titles(list)).toEqual(["B", "C", "D"]);
    expect(groups(list)).toEqual([null, 1, 1]);
  });

  it("rest applies to every member", () => {
    const list = [ex("A", [[1, 1]], 90, 1), ex("B", [[1, 1]], 90, 1)];
    setRest(list, 1, 150);
    expect(list.map((e) => e.rest_seconds)).toEqual([150, 150]);
  });
});

describe("moving", () => {
  it("moves single exercises", () => {
    const list = [ex("A", [[1, 1]]), ex("B", [[1, 1]]), ex("C", [[1, 1]])];
    move(list, 2, -1);
    expect(titles(list)).toEqual(["A", "C", "B"]);
    expect(canMove(list, 0, -1)).toBe(false);
    expect(canMove(list, 2, 1)).toBe(false);
  });

  it("swaps within a superset and keeps the first member's rest", () => {
    const list = [ex("A", [[1, 1]], 60, 1), ex("B", [[1, 1]], 120, 1)];
    move(list, 1, -1);
    expect(titles(list)).toEqual(["B", "A"]);
    expect(list.map((e) => e.rest_seconds)).toEqual([120, 120]);
  });

  it("moves a whole superset past a neighbour, and an exercise past a whole superset", () => {
    const list = [ex("X", [[1, 1]]), ex("A", [[1, 1]], 90, 1), ex("B", [[1, 1]], 90, 1)];
    move(list, 1, -1);
    expect(titles(list)).toEqual(["A", "B", "X"]);
    move(list, 2, -1);
    expect(titles(list)).toEqual(["X", "A", "B"]);
    expect(groups(list)).toEqual([null, 1, 1]);
  });
});

describe("validation and payload", () => {
  const today = "2026-01-23";

  it("requires a title, named exercises and reps", () => {
    const blank = blankExercise();
    const errors = validatePlan({ title: " ", date: today, exercises: [blank] }, { allowFuture: true, today });
    expect(errors.title).toBeDefined();
    expect(errors[`exercise.${blank.key}.title`]).toBeDefined();
    expect(errors[`exercise.${blank.key}.sets`]).toBeDefined();
  });

  it("allows future dates only for plans", () => {
    const list = [ex("Bench", [[150, 5]])];
    const form = { title: "Upper", date: "2026-02-01", exercises: list };
    expect(validatePlan(form, { allowFuture: true, today })).toEqual({});
    expect(validatePlan(form, { allowFuture: false, today }).date).toBeDefined();
  });

  it("marks sets done only for finished sessions and keeps ids", () => {
    const e = { ...ex(" Bench ", [[152.5, 5]]), id: 7 };
    expect(toPayload([e], "planned")).toEqual([
      { id: 7, title: "Bench", sets: [{ weight: 152.5, reps: 5, done: false }], rest_seconds: 90, comments: "", superset_group: null },
    ]);
    expect(toPayload([e], "done")[0]!.sets[0]!.done).toBe(true);
  });

  it("keeps each set's own done flag for a live session", () => {
    const e = ex("Bench", [[150, 5], [155, 5]]);
    e.sets[0]!.done = true;
    expect(toPayload([e], "active")[0]!.sets.map((s) => s.done)).toEqual([true, false]);
    expect(toPayload([e], "new")[0]!.sets.map((s) => s.done)).toEqual([false, false]);
  });
});

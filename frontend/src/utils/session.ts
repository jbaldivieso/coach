import type { Set } from "@/types/lifting";

interface Groupable {
  superset_group: number | null;
}

interface WithSets extends Groupable {
  title: string;
  sets: Set[];
}

/** A run of exercises done together: one exercise, or a superset of adjacent exercises sharing a group. */
export interface Unit<T> {
  start: number; // index of the first exercise in the session
  items: T[];
  isSuperset: boolean;
}

export function groupUnits<T extends Groupable>(exercises: T[]): Unit<T>[] {
  const units: Unit<T>[] = [];
  exercises.forEach((exercise, i) => {
    const last = units[units.length - 1];
    const lastGroup = last?.items[0]?.superset_group ?? null;
    if (last && exercise.superset_group !== null && exercise.superset_group === lastGroup) {
      last.items.push(exercise);
      last.isSuperset = true;
    } else {
      units.push({ start: i, items: [exercise], isSuperset: false });
    }
  });
  return units;
}

/** Number of rounds in a unit: its longest exercise's set count. */
export function roundCount<T extends WithSets>(unit: Unit<T>): number {
  return Math.max(0, ...unit.items.map((e) => e.sets.length));
}

export interface Position {
  unitIndex: number;
  /** Set number within the unit (the round, for a superset). */
  round: number;
  /** Index of the exercise in the session. */
  exerciseIndex: number;
}

/**
 * Where the lifter is within a unit: the first round with an undone set, and
 * within that round the first exercise not yet done. null when the unit is finished.
 */
export function positionInUnit<T extends WithSets>(unit: Unit<T>, unitIndex: number): Position | null {
  const rounds = roundCount(unit);
  for (let round = 0; round < rounds; round++) {
    const i = unit.items.findIndex((e) => e.sets[round] && !e.sets[round]!.done);
    if (i >= 0) return { unitIndex, round, exerciseIndex: unit.start + i };
  }
  return null;
}

/** The first undone set in the session, in order; null when everything is done. */
export function currentPosition<T extends WithSets>(exercises: T[]): Position | null {
  const units = groupUnits(exercises);
  for (let u = 0; u < units.length; u++) {
    const position = positionInUnit(units[u]!, u);
    if (position) return position;
  }
  return null;
}

/** Superset member letter: 0 → "A". */
export function memberLetter(index: number): string {
  return String.fromCharCode(65 + index);
}

/** "Flyes + Lat raises" for a superset, the title for a single exercise. */
export function unitTitle<T extends { title: string }>(unit: Unit<T>): string {
  return unit.items.map((e) => e.title).join(" + ");
}

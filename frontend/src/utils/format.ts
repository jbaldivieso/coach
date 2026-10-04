import type { SetValues } from "@/types/lifting";

const MS_PER_DAY = 24 * 60 * 60 * 1000;

/** Parse "YYYY-MM-DD" as a local date (not UTC, which shifts days in western timezones). */
export function parseDate(iso: string): Date {
  const [y, m, d] = iso.slice(0, 10).split("-").map(Number);
  return new Date(y!, (m ?? 1) - 1, d ?? 1);
}

/** Local date as "YYYY-MM-DD". */
export function toISODate(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

export function todayISO(): string {
  return toISODate(new Date());
}

/** 152.5 → "152.5", 150 → "150", null → "BW". */
export function formatWeight(weight: number | null): string {
  if (weight === null) return "BW";
  return String(Math.round(weight * 100) / 100);
}

/** "150 × 5", "BW × 9". */
export function formatSet(set: SetValues): string {
  return `${formatWeight(set.weight)} × ${set.reps}`;
}

/** "Jan 21" */
export function formatShortDate(iso: string): string {
  return parseDate(iso).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

/** "Wed Jan 21" */
export function formatDayDate(iso: string): string {
  const date = parseDate(iso);
  const weekday = date.toLocaleDateString("en-US", { weekday: "short" });
  return `${weekday} ${formatShortDate(iso)}`;
}

/** "Jan 21 · Upper B" */
export function formatOuting(iso: string, title: string): string {
  return `${formatShortDate(iso)} · ${title}`;
}

/** "Jan 2026" */
export function formatMonthYear(iso: string): string {
  return parseDate(iso).toLocaleDateString("en-US", { month: "short", year: "numeric" });
}

/** Whole calendar days from `iso` to `now` (positive when iso is in the past). */
export function daysAgo(iso: string, now: Date = new Date()): number {
  const then = parseDate(iso);
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  return Math.round((today.getTime() - then.getTime()) / MS_PER_DAY);
}

/** Compact age for list rows: "today", "yesterday", "5 days", "3 wk", "4 mo", "2 yr". */
export function relativeShort(iso: string, now: Date = new Date()): string {
  const days = daysAgo(iso, now);
  if (days <= 0) return "today";
  if (days === 1) return "yesterday";
  if (days < 7) return `${days} days`;
  if (days < 7 * 13) return `${Math.floor(days / 7)} wk`;
  if (days < 365) return `${Math.floor(days / 30)} mo`;
  return `${Math.floor(days / 365)} yr`;
}

/** Full sentence age: "today", "yesterday", "22 days ago", "9 weeks ago", "5 months ago", "2 years ago". */
export function relativeLong(iso: string, now: Date = new Date()): string {
  const days = daysAgo(iso, now);
  if (days <= 0) return "today";
  if (days === 1) return "yesterday";
  if (days < 45) return `${days} days ago`;
  if (days < 7 * 17) return `${Math.floor(days / 7)} weeks ago`;
  if (days < 365 * 2) return `${Math.floor(days / 30)} months ago`;
  return `${Math.floor(days / 365)} years ago`;
}

/** 240 → "4:00", 75 → "1:15", -3 → "0:00". */
export function formatClock(seconds: number): string {
  const s = Math.max(0, Math.round(seconds));
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

/** Parse "1:30" or "90" into seconds; null if it isn't a time. */
export function parseClock(text: string): number | null {
  const trimmed = text.trim();
  const match = trimmed.match(/^(\d+):([0-5]?\d)$/);
  if (match) return Number(match[1]) * 60 + Number(match[2]);
  if (/^\d+$/.test(trimmed)) return Number(trimmed);
  return null;
}

/** "Bench · Pull-ups · Incline press" */
export function formatExerciseList(exercises: { title: string }[]): string {
  return exercises.map((e) => e.title).join(" · ");
}

/** "1 time", "4 times" */
export function pluralize(count: number, singular: string, plural = `${singular}s`): string {
  return `${count} ${count === 1 ? singular : plural}`;
}

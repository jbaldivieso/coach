import { describe, it, expect } from "vitest";
import {
  parseDate,
  toISODate,
  formatWeight,
  formatSet,
  formatShortDate,
  formatDayDate,
  formatOuting,
  daysAgo,
  relativeShort,
  relativeLong,
  formatClock,
  parseClock,
  pluralize,
} from "./format";

const now = new Date(2026, 0, 23, 18, 30); // Fri Jan 23 2026, evening

describe("dates", () => {
  it("parses ISO dates as local days", () => {
    const d = parseDate("2026-01-21");
    expect([d.getFullYear(), d.getMonth(), d.getDate()]).toEqual([2026, 0, 21]);
    expect(toISODate(d)).toBe("2026-01-21");
  });

  it("formats short and day dates", () => {
    expect(formatShortDate("2026-01-21")).toBe("Jan 21");
    expect(formatDayDate("2026-01-21")).toBe("Wed Jan 21");
    expect(formatOuting("2026-01-21", "Upper B")).toBe("Jan 21 · Upper B");
  });

  it("counts whole days regardless of time of day", () => {
    expect(daysAgo("2026-01-23", now)).toBe(0);
    expect(daysAgo("2026-01-21", now)).toBe(2);
  });

  it("gives compact relative times", () => {
    expect(relativeShort("2026-01-23", now)).toBe("today");
    expect(relativeShort("2026-01-22", now)).toBe("yesterday");
    expect(relativeShort("2026-01-18", now)).toBe("5 days");
    expect(relativeShort("2026-01-09", now)).toBe("2 wk");
    expect(relativeShort("2025-07-01", now)).toBe("6 mo");
    expect(relativeShort("2023-01-01", now)).toBe("3 yr");
  });

  it("gives sentence relative times", () => {
    expect(relativeLong("2026-01-01", now)).toBe("22 days ago");
    expect(relativeLong("2025-11-01", now)).toBe("11 weeks ago");
    expect(relativeLong("2025-06-01", now)).toBe("7 months ago");
    expect(relativeLong("2023-01-01", now)).toBe("3 years ago");
  });
});

describe("sets", () => {
  it("formats weights, including bodyweight and decimals", () => {
    expect(formatWeight(null)).toBe("BW");
    expect(formatWeight(150)).toBe("150");
    expect(formatWeight(152.5)).toBe("152.5");
    expect(formatSet({ weight: 150, reps: 5 })).toBe("150 × 5");
    expect(formatSet({ weight: null, reps: 9 })).toBe("BW × 9");
  });
});

describe("clock", () => {
  it("formats m:ss", () => {
    expect(formatClock(240)).toBe("4:00");
    expect(formatClock(75)).toBe("1:15");
    expect(formatClock(-3)).toBe("0:00");
  });

  it("parses m:ss or plain seconds", () => {
    expect(parseClock("1:30")).toBe(90);
    expect(parseClock("90")).toBe(90);
    expect(parseClock("abc")).toBeNull();
    expect(parseClock("1:75")).toBeNull();
  });
});

it("pluralizes", () => {
  expect(pluralize(1, "set")).toBe("1 set");
  expect(pluralize(4, "set")).toBe("4 sets");
});

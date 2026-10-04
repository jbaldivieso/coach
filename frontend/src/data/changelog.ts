export interface Change {
  title: string;
  description?: string;
}

export interface ChangeGroup {
  date: string; // "YYYY-MM-DD"
  changes: Change[];
}

/** Newest first. The first group drives the unread dot on the ⋯ menu. */
export const changelog: ChangeGroup[] = [
  {
    date: "2026-02-05",
    changes: [
      {
        title: "Quick clear for comment fields",
        description:
          "If you clone a session, we add a comment with the last time's stats. Now you can delete that more easily when you want.",
      },
      {
        title: "Better exercise handling",
        description:
          "When working on a session, you can now re-order the exercises and expand and collapse them to save space.",
      },
    ],
  },
  {
    date: "2026-01-31",
    changes: [
      {
        title: "New approach to sets: weight can change as well as reps!",
        description: "OUR NUMBER 1 MOST REQUESTED FEATURE!!!",
      },
      {
        title: "Search sessions and exercises",
        description: "Want to see how your benching efforts have changed over time? Search it up!",
      },
      {
        title: "Session calendar",
        description: "Get sense of when your workouts have been",
      },
    ],
  },
];

const SEEN_KEY = "coach.changelog.seen";

export function latestChangeDate(): string | null {
  return changelog[0]?.date ?? null;
}

/** Storage can be unavailable (private mode, blocked site data); treat that as "seen" so the dot never nags. */
export function hasUnreadChanges(): boolean {
  const latest = latestChangeDate();
  if (!latest) return false;
  try {
    const seen = localStorage.getItem(SEEN_KEY);
    return seen === null || seen < latest;
  } catch {
    return false;
  }
}

export function markChangesSeen(): void {
  const latest = latestChangeDate();
  if (!latest) return;
  try {
    localStorage.setItem(SEEN_KEY, latest);
  } catch {
    // Nothing to do; the dot just stays.
  }
}

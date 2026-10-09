export interface Change {
  title: string;
  description?: string;
}

export interface ChangeGroup {
  date: string; // "YYYY-MM-DD"
  /** A few words for the ⋯ menu. */
  teaser?: string;
  changes: Change[];
}

/** Newest first. The first group drives the unread dot on the ⋯ menu. */
export const changelog: ChangeGroup[] = [
  {
    date: "2026-10-09",
    teaser: "Edit mid-session, fold, notes, COACH",
    changes: [
      {
        title: "Change the plan without leaving the gym floor",
        description:
          "Flip Track from Lift to Edit to reorder, add, drop, or superset what's left. Sets you've already done stay locked, so no rewriting history. Back to lifting saves it, and the rest timer keeps counting (and yelling) the whole time.",
      },
      {
        title: "Fold an exercise when it's planned",
        description:
          "The open exercise's header sticks to the top, keyboard up or not, with a fold button. Fold it and the whole plan reads as a list, sets and rest at a glance.",
      },
      {
        title: "Notes on the whole session",
        description:
          "Jot a session note while planning, or tap \"Note on today\" between sets. It's waiting for you on Finish.",
      },
      {
        title: "COACH takes you home",
        description: "From any screen. The back arrow only shows up when it goes somewhere else.",
      },
    ],
  },
  {
    date: "2026-10-04",
    teaser: "New look, planning, live tracking, supersets",
    changes: [
      {
        title: "A whole new Coach. It's yellow now.",
        description:
          "New look, top to bottom. Yellow means something is happening right now: the current set, the Done button, the rest timer. Everything else stays out of your way.",
      },
      {
        title: "Plan on your phone, in about a minute",
        description:
          "Start blank or from any past session. Every exercise shows its last 3 outings right there, so you can decide whether today's the day for 155. Tap a set to change it, or Save for later and plan from the laptop.",
      },
      {
        title: "Live tracking, one tap per set",
        description:
          "Hit Done and the set is saved, the rest timer starts, and you're on to the next one. Kill the app mid-workout, iOS? Go ahead. Resume picks up at the right set, and even the right second of rest.",
      },
      {
        title: "Supersets",
        description: "Link two exercises and they share one rest. Do A, do B, rest. Repeat until regret.",
      },
      {
        title: "Look back properly",
        description:
          "Tap any exercise name to see every time you've done it, with a chart. Tap the month on Home to see the whole year. Search answers \"when did I last…\" before you even scroll.",
      },
      {
        title: "Goodbye, session types",
        description: "Nobody will miss them. Not even Recovery.",
      },
    ],
  },
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

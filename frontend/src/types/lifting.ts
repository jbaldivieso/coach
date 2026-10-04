export interface Set {
  weight: number | null; // null means bodyweight
  reps: number;
  done: boolean;
}

/** Just the numbers of a set, for display. */
export type SetValues = Pick<Set, "weight" | "reps">;

export type SessionStatus = "planned" | "active" | "done";

export interface Exercise {
  id: number;
  title: string;
  sets: Set[];
  rest_seconds: number;
  comments: string;
  position: number;
  superset_group: number | null;
}

export interface Session {
  id: number;
  title: string;
  date: string;
  comments: string;
  status: SessionStatus;
  started_at: string | null;
  finished_at: string | null;
  exercises: Exercise[];
}

export interface PaginatedSessions {
  items: Session[];
  total: number;
  has_more: boolean;
}

/** Payload shape for an exercise when saving a whole session. */
export interface ExercisePayload {
  id?: number;
  title: string;
  sets: Set[];
  rest_seconds: number;
  comments: string;
  superset_group: number | null;
}

// History and search

export interface TitleSuggestion {
  title: string;
  count: number;
  last_date: string | null;
}

export interface TitleSuggestions {
  suggestions: TitleSuggestion[];
}

export interface Outing {
  exercise_id: number;
  session_id: number;
  session_title: string;
  date: string;
  sets: Set[];
  rest_seconds: number;
  comments: string;
}

export interface ExerciseHistory {
  title: string;
  items: Outing[];
  total: number;
  has_more: boolean;
}

export interface SessionSummary {
  id: number;
  title: string;
  date: string;
}

export interface SearchResponse {
  sessions: SessionSummary[];
  exercises: TitleSuggestion[];
  last_session: SessionSummary | null;
}

// Calendar

export interface SessionDate {
  date: string;
  session_id: number;
}

export interface CalendarMonth {
  year: number;
  month: number;
  sessions: SessionDate[];
}

export interface CalendarYear {
  months: CalendarMonth[];
}

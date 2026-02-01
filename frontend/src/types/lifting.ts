export interface Set {
  weight: number | null;
  reps: number;
}

export interface SetFormData {
  weight: string; // "" for bodyweight
  reps: string;
}

export interface Exercise {
  id: number;
  title: string;
  sets: Set[];
  rest_seconds: number;
  comments: string;
}

export interface Session {
  id: number;
  title: string;
  date: string;
  comments: string;
  session_type: string;
  exercises: Exercise[];
}

export interface PaginatedSessions {
  items: Session[];
  total: number;
  has_more: boolean;
}

export interface ExerciseFormData {
  title: string;
  sets: SetFormData[];
  rest_seconds: string;
  comments: string;
}

export interface ExerciseEditState {
  id?: number;
  data: ExerciseFormData;
}

export interface SessionFormData {
  title: string;
  date: string;
  session_type: string;
  comments: string;
}

export type SessionType = "volume" | "weight" | "endurance" | "recovery";

export const SESSION_TYPES: { value: SessionType; label: string }[] = [
  { value: "volume", label: "Volume" },
  { value: "weight", label: "Weight" },
  { value: "endurance", label: "Endurance" },
  { value: "recovery", label: "Recovery" },
];

// Search types
export interface AutocompleteItem {
  type: "session" | "exercise";
  id: number | null;
  label: string;
  value: string;
}

export interface AutocompleteResponse {
  items: AutocompleteItem[];
}

export interface SearchResult {
  exercise_id: number;
  exercise_title: string;
  sets: Set[];
  rest_seconds: number;
  session_id: number;
  session_date: string;
  session_title: string;
}

export interface SearchResultsResponse {
  items: SearchResult[];
  total: number;
}

export interface SearchFilter {
  type: "session" | "exercise";
  id: number | null;
  label: string;
  value: string;
}

// Calendar types
export interface SessionDate {
  date: string;
  session_id: number;
}

export interface CalendarMonth {
  year: number;
  month: number;
  sessions: SessionDate[];
}

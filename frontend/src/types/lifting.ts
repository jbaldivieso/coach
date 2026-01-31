export interface Exercise {
  id: number;
  title: string;
  weight_lbs: number | null;
  rest_seconds: number;
  reps: number[];
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
  weight_lbs: string;
  rest_seconds: string;
  reps: string;
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
  weight_lbs: number | null;
  reps: number[];
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

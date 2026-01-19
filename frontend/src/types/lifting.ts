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

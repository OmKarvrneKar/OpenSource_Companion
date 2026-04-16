export type SkillLevel = "beginner" | "intermediate" | "advanced";

export interface User {
  id: number;
  github_username: string;
  email: string | null;
  avatar_url: string | null;
  skill_level: SkillLevel;
  primary_language: string | null;
  points_total: number;
  is_mentor: boolean;
}

export interface Issue {
  id: number;
  title: string;
  description: string | null;
  difficulty: SkillLevel;
  language: string | null;
  state: "open" | "closed";
  github_url: string | null;
  comment_count: number;
  days_open: number;
  repo_name?: string;
  match_score?: number;
}

export type EnrollmentStatus = "enrolled" | "completed" | "dropped" | "stale";

export interface Enrollment {
  id: number;
  user_id: number;
  issue_id: number;
  status: EnrollmentStatus;
  pr_url: string | null;
  enrolled_at: string;
  completed_at: string | null;
  issue?: Issue;
}

export interface Badge {
  id: number;
  name: string;
  description: string;
  trigger_condition: string;
  icon_url: string | null;
}

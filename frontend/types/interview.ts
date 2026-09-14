import type { SessionStatus } from "@/lib/sessionStatus";

export interface Evaluation {
  score: number;
  level: string;
  strengths: string[];
  weaknesses: string[];
  feedback: string;
  concept_gaps: string[];
  follow_up_question: string;
}

export interface InterviewState {
  sessionId: number | null;
  questionId: number | null;

  role: string;

  question: string;

  answer: string;

  evaluation: Evaluation | null;

  loading: boolean;

  difficulty: number;

  questionNumber: number;

  totalQuestions: number;

  finished: boolean;

  overallScore?: number;

  recommendation?: string;
}

// Backend history/session response (mapped to camelCase in frontend).
// `status` is normalized by `lib/sessionStatus` so the UI never compares raw
// backend strings - that mismatch is what zeroed out the dashboard analytics.
export interface SessionSummary {
  id: number;
  role: string;
  status: SessionStatus;
  overallScore?: number | null;
  recommendation?: string | null;
}

export interface SessionDetails {
  id: number;
  userId?: number | null;
  role?: string;
  status?: SessionStatus;
  sessionId?: number | null;
  questionId?: number | null;
  currentDifficulty?: number | null;
  currentQuestion?: string | null;
  questions?: string[];
  answers?: string[];
  questionNumber?: number | null;
  evaluations?: any[];
  overallScore?: number | null;
  recommendation?: string | null;
  pdfPath?: string | null;
}
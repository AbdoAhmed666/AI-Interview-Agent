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

// Backend history/session response (mapped to camelCase in frontend)
export interface SessionSummary {
  id: number;
  role: string;
  status: string;
  overallScore?: number | null;
  recommendation?: string | null;
}

export interface SessionDetails {
  id: number;
  userId?: number | null;
  role?: string;
  status?: string;
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
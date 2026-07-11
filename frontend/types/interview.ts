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
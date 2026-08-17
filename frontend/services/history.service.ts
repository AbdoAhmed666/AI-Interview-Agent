import api from "@/lib/axios";
import type { SessionSummary, SessionDetails } from "@/types/interview";

export async function getMySessions(): Promise<SessionSummary[]> {
  const { data } = await api.get("/my-sessions");

  // Map backend snake_case -> frontend camelCase
  const sessions = (data || []).map((s: any) => ({
    id: s.id,
    role: s.role,
    status: s.status,
    overallScore: s.overall_score ?? null,
    recommendation: s.recommendation ?? null,
  } as SessionSummary));

  return sessions;
}

export async function getSession(id: number): Promise<SessionDetails> {
  const { data } = await api.get(`/session/${id}`);

  if (!data) return {} as SessionDetails;

  const mapped: SessionDetails = {
    id: data.id ?? data.session_id,
    userId: data.user_id ?? null,
    role: data.role,
    status: data.status ?? (data.evaluations && data.evaluations.length ? "completed" : "in-progress"),
    sessionId: data.session_id ?? null,
    questionId: data.question_id ?? null,
    currentDifficulty: data.current_difficulty ?? null,
    currentQuestion: data.current_question ?? null,
    questions: data.questions ?? [],
    answers: data.answers ?? [],
    questionNumber: data.question_number ?? null,
    evaluations: data.evaluations ?? [],
    overallScore: data.overall_score ?? null,
    recommendation: data.recommendation ?? null,
    pdfPath: data.pdf_path ?? null,
  };

  return mapped;
}
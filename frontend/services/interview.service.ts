import api from "@/lib/axios";

export async function startInterview(role: string) {
  const { data } = await api.post("/start-interview", {
    role,
  });

  return data;
}

export async function evaluateAnswer(
  sessionId: number,
  questionId: number,
  answer: string
) {
  const { data } = await api.post(
    "/adaptive-interview",
    {
      session_id: sessionId,
      question_id: questionId,
      answer,
    }
  );

  return data;
}

export async function finishInterview(
  sessionId: number
) {
  const { data } = await api.post(
    "/finish-interview",
    {
      session_id: sessionId,
    }
  );

  return data;
}

export async function downloadReport(body:any){
  // Download handled by report.service to centralize blob handling
  // Keep this as a thin proxy for backward compatibility
  const { downloadReport } = await import("./report.service");
  return downloadReport(body);
}
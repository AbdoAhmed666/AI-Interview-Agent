import api from "@/lib/axios";

export async function startInterview(role: string) {
  const { data } = await api.post("/start-interview", {
    role,
  });

  return data;
}

export async function evaluateAnswer(
  questionId: number,
  answer: string
) {
  const { data } = await api.post(
    "/adaptive-interview",
    {
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

    const response=await api.post(
        "/download-report",
        body,
        {
            responseType:"blob",
        }
    );

    return response.data;
}
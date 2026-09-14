import { act, renderHook, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import useInterview from "@/hooks/useInterview";

const {
  startInterview,
  evaluateAnswer,
  finishInterview,
  getActiveInterview,
} = vi.hoisted(() => ({
  startInterview: vi.fn(),
  evaluateAnswer: vi.fn(),
  finishInterview: vi.fn(),
  getActiveInterview: vi.fn(),
}));

vi.mock("@/services/interview.service", () => ({
  startInterview,
  evaluateAnswer,
  finishInterview,
  getActiveInterview,
}));

const EVALUATION = { score: 8, level: "strong", feedback: "Good answer." };

beforeEach(() => {
  vi.clearAllMocks();
  getActiveInterview.mockResolvedValue({ active: false });
});

async function startedInterview() {
  startInterview.mockResolvedValue({
    eligible: true,
    session_id: 23,
    question_id: 44,
    question: "Q1?",
  });

  const { result } = renderHook(() => useInterview());

  await act(async () => {
    await result.current.start("backend");
  });

  return result;
}

describe("start", () => {
  it("loads the first question", async () => {
    const result = await startedInterview();

    expect(result.current.sessionId).toBe(23);
    expect(result.current.questionId).toBe(44);
    expect(result.current.question).toBe("Q1?");
    expect(result.current.questionNumber).toBe(1);
    expect(result.current.finished).toBe(false);
  });
});

describe("submit", () => {
  it("shows the evaluation and moves on to the next question", async () => {
    const result = await startedInterview();
    evaluateAnswer.mockResolvedValue({
      status: "ACTIVE",
      evaluation: EVALUATION,
      next_question: "Q2?",
      question_id: 45,
      difficulty: 4,
    });

    act(() => result.current.setAnswer("my answer"));
    await act(async () => {
      await result.current.submit();
    });

    expect(evaluateAnswer).toHaveBeenCalledWith(23, 44, "my answer");
    expect(result.current.evaluation).toEqual(EVALUATION);
    expect(result.current.question).toBe("Q2?");
    expect(result.current.questionId).toBe(45);
    expect(result.current.questionNumber).toBe(2);
    expect(result.current.difficulty).toBe(4);
    expect(result.current.answer).toBe("");
  });

  it("keeps the question and the typed answer when no next question comes back", async () => {
    // A duplicate submit landing while the first evaluation is still running
    // returns 200 with next_question: null. Blanking the card on that response
    // is what made the interview look like it had vanished.
    const result = await startedInterview();
    evaluateAnswer.mockResolvedValue({
      status: "EVALUATING",
      already_submitted: true,
      evaluation: null,
      next_question: null,
    });

    act(() => result.current.setAnswer("my answer"));
    await act(async () => {
      await result.current.submit();
    });

    expect(result.current.question).toBe("Q1?");
    expect(result.current.questionId).toBe(44);
    expect(result.current.questionNumber).toBe(1);
    expect(result.current.answer).toBe("my answer");
    expect(result.current.error).toMatch(/still being evaluated/i);
    expect(finishInterview).not.toHaveBeenCalled();
  });

  it("finishes the interview on READY_TO_FINISH", async () => {
    const result = await startedInterview();
    evaluateAnswer.mockResolvedValue({
      status: "READY_TO_FINISH",
      evaluation: EVALUATION,
      next_question: null,
    });
    finishInterview.mockResolvedValue({
      overall_score: 7.4,
      recommendation: "Hire",
    });

    act(() => result.current.setAnswer("last answer"));
    await act(async () => {
      await result.current.submit();
    });

    expect(finishInterview).toHaveBeenCalledWith(23);
    expect(result.current.finished).toBe(true);
    expect(result.current.overallScore).toBe(7.4);
    expect(result.current.recommendation).toBe("Hire");
    // The feedback on the final answer is still shown.
    expect(result.current.evaluation).toEqual(EVALUATION);
  });

  it("surfaces a failure without losing the question", async () => {
    const result = await startedInterview();
    evaluateAnswer.mockRejectedValue(new Error("network down"));

    act(() => result.current.setAnswer("my answer"));
    await act(async () => {
      await result.current.submit();
    });

    expect(result.current.error).toBeTruthy();
    expect(result.current.question).toBe("Q1?");
    expect(result.current.loading).toBe(false);
  });

  it("does nothing without a session", async () => {
    const { result } = renderHook(() => useInterview());

    await act(async () => {
      await result.current.submit();
    });

    expect(evaluateAnswer).not.toHaveBeenCalled();
  });
});

describe("resume", () => {
  it("rebuilds the interview from the server after a reload", async () => {
    getActiveInterview.mockResolvedValue({
      active: true,
      session_id: 23,
      role: "backend",
      status: "ACTIVE",
      question_id: 44,
      question: "Q3?",
      question_number: 3,
      total_questions: 5,
      difficulty: 4,
      evaluation: EVALUATION,
    });

    const { result } = renderHook(() => useInterview());

    await act(async () => {
      await result.current.resume();
    });

    expect(result.current.sessionId).toBe(23);
    expect(result.current.role).toBe("backend");
    expect(result.current.question).toBe("Q3?");
    expect(result.current.questionId).toBe(44);
    expect(result.current.questionNumber).toBe(3);
    expect(result.current.difficulty).toBe(4);
    // The feedback on the previous answer survives the reload too.
    expect(result.current.evaluation).toEqual(EVALUATION);
  });

  it("leaves the start screen alone when there is nothing to resume", async () => {
    const { result } = renderHook(() => useInterview());

    await act(async () => {
      await result.current.resume();
    });

    expect(result.current.sessionId).toBeNull();
    expect(result.current.question).toBe("");
  });

  it("resolves a session that is already ready to finish", async () => {
    getActiveInterview.mockResolvedValue({
      active: true,
      session_id: 23,
      role: "backend",
      status: "READY_TO_FINISH",
      question_id: 48,
      question: null,
      question_number: 5,
      evaluation: EVALUATION,
    });
    finishInterview.mockResolvedValue({
      overall_score: 8.2,
      recommendation: "Strong hire",
    });

    const { result } = renderHook(() => useInterview());

    await act(async () => {
      await result.current.resume();
    });

    expect(result.current.finished).toBe(true);
    expect(result.current.overallScore).toBe(8.2);
  });

  it("warns instead of stealing an evaluation another worker is running", async () => {
    getActiveInterview.mockResolvedValue({
      active: true,
      session_id: 23,
      role: "backend",
      status: "PENDING_EVALUATION",
      question_id: 44,
      question: "Q3?",
      question_number: 3,
      evaluation: null,
    });

    const { result } = renderHook(() => useInterview());

    await act(async () => {
      await result.current.resume();
    });

    expect(result.current.question).toBe("Q3?");
    expect(result.current.error).toMatch(/still being evaluated/i);
  });

  it("never clobbers an interview this tab already has open", async () => {
    const result = await startedInterview();

    await act(async () => {
      await result.current.resume();
    });

    expect(getActiveInterview).not.toHaveBeenCalled();
    expect(result.current.question).toBe("Q1?");
  });

  it("only asks the server once per mount", async () => {
    const { result } = renderHook(() => useInterview());

    await act(async () => {
      await Promise.all([result.current.resume(), result.current.resume()]);
    });
    await act(async () => {
      await result.current.resume();
    });

    await waitFor(() => expect(getActiveInterview).toHaveBeenCalledTimes(1));
  });
});

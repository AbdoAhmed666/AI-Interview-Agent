"use client";

import { useRef, useState } from "react";

import {
  startInterview,
  evaluateAnswer,
  finishInterview,
  getActiveInterview,
} from "@/services/interview.service";
import { getApiErrorMessage } from "@/lib/apiError";

export default function useInterview() {
  const [sessionId, setSessionId] = useState<number | null>(null);

  const [questionId, setQuestionId] = useState<number | null>(null);

  const [role, setRole] = useState("");

  const [question, setQuestion] = useState("");

  const [answer, setAnswer] = useState("");

  const [evaluation, setEvaluation] = useState<any>(null);

  const [loading, setLoading] = useState(false);

  const [difficulty, setDifficulty] = useState(3);

  const [questionNumber, setQuestionNumber] = useState(0);

  const totalQuestions = 5;

  const [finished, setFinished] = useState(false);

  const [overallScore, setOverallScore] = useState<number>();

  const [recommendation, setRecommendation] = useState("");

  const [error, setError] = useState("");

  const [resuming, setResuming] = useState(false);

  // Resuming is attempted once per mount; React runs effects twice in
  // development, and a second call would race the first.
  const resumeAttempted = useRef(false);

  //--------------------------------

  /**
   * Rebuild an unfinished interview from the server.
   *
   * Interview progress is durable in PostgreSQL, but this hook holds it in
   * React state, so a page reload used to lose the session entirely and strand
   * it as "in progress" forever. Best-effort: if anything fails the candidate
   * simply gets the normal start screen.
   */
  async function resume() {
    if (resumeAttempted.current || sessionId !== null || finished) {
      return;
    }

    resumeAttempted.current = true;
    setResuming(true);

    try {
      const data = await getActiveInterview();

      if (!data?.active) {
        return;
      }

      setSessionId(data.session_id);
      setRole(data.role ?? "");
      setEvaluation(data.evaluation ?? null);
      setDifficulty(data.difficulty ?? 3);
      setAnswer("");

      if (data.status === "READY_TO_FINISH") {
        const result = await finishInterview(data.session_id);

        setQuestionNumber(data.question_number ?? totalQuestions);
        setOverallScore(result.overall_score);
        setRecommendation(result.recommendation);
        setFinished(true);
        return;
      }

      setQuestionId(data.question_id ?? null);
      setQuestion(data.question ?? "");
      setQuestionNumber(data.question_number ?? 1);

      if (data.status === "PENDING_EVALUATION") {
        setError(
          "Your last answer is still being evaluated. Please refresh in a moment to continue.",
        );
      }
    } catch {
      // Leave the start screen in place, and allow a later retry.
      resumeAttempted.current = false;
    } finally {
      setResuming(false);
    }
  }

  //--------------------------------

  async function start(roleName: string) {
    setLoading(true);
    setError("");

    try {
      const data = await startInterview(roleName);

      if (data?.eligible !== false) {
        setRole(roleName);

        setSessionId(data.session_id);

        setQuestionId(data.question_id);

        setQuestion(data.question ?? data.next_question ?? data.first_question);

        setQuestionNumber(1);

        setEvaluation(null);

        setAnswer("");

        setFinished(false);

        setDifficulty(3);
      }

      return data;
    } finally {
      setLoading(false);
    }
  }

  //--------------------------------

  async function submit() {
    if (!questionId || !sessionId) return;

    setLoading(true);
    setError("");

    try {
      const data = await evaluateAnswer(sessionId, questionId, answer);

      // Show the AI's feedback on the answer just submitted (returned for
      // every question, including the last).
      setEvaluation(data.evaluation ?? null);

      // The backend ends the interview by returning READY_TO_FINISH (there is
      // no sixth question); the answered-count is a defensive fallback, and it
      // only applies once this answer really was evaluated.
      const isFinished =
        data?.status === "READY_TO_FINISH" ||
        (questionNumber >= totalQuestions && Boolean(data?.evaluation));

      if (isFinished) {
        setAnswer("");

        const result = await finishInterview(sessionId);

        // Backend returns overall_score / recommendation.
        setOverallScore(result.overall_score);
        setRecommendation(result.recommendation);
        setFinished(true);
        return;
      }

      if (!data?.next_question) {
        // The answer was accepted but no next question came back - e.g. a
        // duplicate submit arriving while the first evaluation is still in
        // flight. Keep the current question (and what was typed) on screen
        // instead of blanking the card.
        setError(
          "Your answer is still being evaluated. Please wait a moment and submit again.",
        );
        return;
      }

      setAnswer("");

      setDifficulty(data.difficulty ?? difficulty);
      setQuestion(data.next_question);
      setQuestionId(data.question_id);
      setQuestionNumber((q) => q + 1);
    } catch (err) {
      setError(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  //--------------------------------

  function reset() {
    setSessionId(null);

    setQuestionId(null);

    setRole("");

    setQuestion("");

    setAnswer("");

    setEvaluation(null);

    setQuestionNumber(0);

    setDifficulty(3);

    setFinished(false);

    setOverallScore(undefined);

    setRecommendation("");

    setError("");

    resumeAttempted.current = false;
  }

  return {
    sessionId,

    role,

    setRole,

    question,

    answer,

    setAnswer,

    evaluation,

    difficulty,

    loading,

    questionNumber,

    totalQuestions,

    finished,

    overallScore,

    recommendation,

    error,

    resuming,

    start,

    submit,

    resume,

    reset,
  };
}

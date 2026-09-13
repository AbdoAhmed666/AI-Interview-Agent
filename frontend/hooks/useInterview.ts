"use client";

import { useState } from "react";

import {
  startInterview,
  evaluateAnswer,
  finishInterview,
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

      setAnswer("");

      // The backend ends the interview by returning READY_TO_FINISH (there is
      // no sixth question); the answered-count is a defensive fallback.
      const isFinished =
        data?.status === "READY_TO_FINISH" ||
        questionNumber >= totalQuestions;

      if (isFinished) {
        const result = await finishInterview(sessionId);

        // Backend returns overall_score / recommendation.
        setOverallScore(result.overall_score);
        setRecommendation(result.recommendation);
        setFinished(true);
        return;
      }

      setEvaluation(data.evaluation ?? null);
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
  }

  return {
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

    start,

    submit,

    reset,
  };
}

"use client";

import { useState } from "react";

import {
  startInterview,
  evaluateAnswer,
  finishInterview,
} from "@/services/interview.service";

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

  //--------------------------------

  async function start(roleName: string) {
    setLoading(true);

    try {
      const data = await startInterview(roleName);

      setRole(roleName);

      setSessionId(data.session_id);

      setQuestionId(data.question_id);

      setQuestion(data.question);

      setQuestionNumber(1);

      setEvaluation(null);

      setAnswer("");

      setFinished(false);

      setDifficulty(3);
    } finally {
      setLoading(false);
    }
  }

  //--------------------------------

  async function submit() {
    if (!questionId) return;

    setLoading(true);

    try {
      const data = await evaluateAnswer(
        questionId,
        answer
      );

      setEvaluation(data.evaluation);

      setDifficulty(data.difficulty);

      setAnswer("");

      if (questionNumber >= totalQuestions) {
        const result = await finishInterview(
          sessionId!
        );

        setFinished(true);

        window.location.href="/history";

        setOverallScore(result.overall_score);

        setRecommendation(result.recommendation);

        return;
      }

      setQuestion(data.next_question);

      setQuestionId(data.question_id);

      setQuestionNumber((q) => q + 1);
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

    start,

    submit,

    reset,
  };
}
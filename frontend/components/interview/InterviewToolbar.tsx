"use client";

import { useInterview } from "@/contexts/InterviewContext";

export default function InterviewToolbar() {

  const {
    questionNumber,
    totalQuestions,
    difficulty,
  } = useInterview();


  return (
    <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-5 flex justify-between">

      <div>
        <h2 className="text-2xl font-bold">
          Technical Interview
        </h2>

        <p className="text-gray-400">
          Practice with AI
        </p>
      </div>

      <div className="flex gap-8">

        <div>
          <p className="text-sm text-gray-400">
            Question
          </p>

          <h3 className="font-bold">
            {questionNumber} / {totalQuestions}
          </h3>
        </div>

        <div>
          <p className="text-sm text-gray-400">
            Difficulty
          </p>

          <h3 className="font-bold">
            {difficulty}
          </h3>
        </div>

      </div>

    </div>
  );
}
"use client";

import { useInterview } from "@/contexts/InterviewContext";

export default function QuestionCard() {

  const { question } = useInterview();

  return (
    <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6 min-h-48">

      <h3 className="font-semibold mb-5">
        AI Question
      </h3>

      <p className="text-lg leading-8 text-gray-300">

        {question || "Click Start Interview to generate your first question."}

      </p>

    </div>
  );
}
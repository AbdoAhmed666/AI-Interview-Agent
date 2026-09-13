"use client";

import Button from "../ui/Button";
import { useInterview } from "@/contexts/InterviewContext";

export default function AnswerEditor() {

    const {
        answer,
        setAnswer,
        submit,
        loading,
        question,
        finished,
        error,
    } = useInterview();

    const disabled = !question || finished;

    return (

        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6">

            <h3 className="font-semibold mb-5">
                Your Answer
            </h3>

            <textarea
                rows={8}
                value={answer}
                disabled={disabled}
                onChange={(e)=>setAnswer(e.target.value)}
                className="w-full rounded-xl border border-[var(--border)] bg-[var(--background)] p-4 resize-none disabled:opacity-50"
            />

            <Button
                className="mt-5"
                onClick={submit}
                disabled={loading || disabled || !answer.trim()}
            >
                {loading ? "Submitting..." : "Submit Answer"}
            </Button>

            {error && (
                <p className="mt-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                    {error}
                </p>
            )}

        </div>

    );

}
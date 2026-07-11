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
    } = useInterview();

    return (

        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6">

            <h3 className="font-semibold mb-5">
                Your Answer
            </h3>

            <textarea
                rows={8}
                value={answer}
                disabled={!question}
                onChange={(e)=>setAnswer(e.target.value)}
                className="w-full rounded-xl border border-[var(--border)] bg-[var(--background)] p-4 resize-none"
            />

            <Button
                className="mt-5"
                onClick={submit}
                disabled={loading || !question}
            >
                {loading ? "Submitting..." : "Submit Answer"}
            </Button>

        </div>

    );

}
"use client";

import { useInterview } from "@/contexts/InterviewContext";

export default function EvaluationPanel(){

    const { evaluation } = useInterview();

    if(!evaluation){

        return(

            <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6">

                <h3 className="font-semibold mb-4">
                    AI Evaluation
                </h3>

                <p className="text-gray-400">
                    Evaluation will appear here after submitting your answer.
                </p>

            </div>

        );

    }

    return(

        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6 space-y-4">

            <h3 className="text-xl font-bold">
                AI Evaluation
            </h3>

            <div>

                <b>Score:</b> {evaluation.score}/10

            </div>

            <div>

                <b>Level:</b> {evaluation.level}

            </div>

            <div>

                <b>Feedback:</b>

                <p className="mt-2 text-gray-300">
                    {evaluation.feedback}
                </p>

            </div>

        </div>

    );

}
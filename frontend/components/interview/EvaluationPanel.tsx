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

    const strengths: string[] = Array.isArray(evaluation.strengths) ? evaluation.strengths : [];
    const weaknesses: string[] = Array.isArray(evaluation.weaknesses) ? evaluation.weaknesses : [];
    const conceptGaps: string[] = Array.isArray(evaluation.concept_gaps) ? evaluation.concept_gaps : [];

    return(

        <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6 space-y-4">

            <h3 className="text-xl font-bold">
                AI Evaluation
            </h3>

            <div className="flex flex-wrap gap-6">

                <div><b>Score:</b> {evaluation.score}/10</div>

                <div><b>Level:</b> {evaluation.level}</div>

            </div>

            <div>

                <b>Feedback:</b>

                <p className="mt-1 text-gray-300">
                    {evaluation.feedback}
                </p>

            </div>

            {strengths.length > 0 && (
                <div>
                    <b>Strengths:</b>
                    <ul className="mt-1 list-disc pl-5 text-gray-300">
                        {strengths.map((item, i) => <li key={i}>{item}</li>)}
                    </ul>
                </div>
            )}

            {weaknesses.length > 0 && (
                <div>
                    <b>Weaknesses:</b>
                    <ul className="mt-1 list-disc pl-5 text-gray-300">
                        {weaknesses.map((item, i) => <li key={i}>{item}</li>)}
                    </ul>
                </div>
            )}

            {conceptGaps.length > 0 && (
                <div>
                    <b>Concept gaps:</b>
                    <ul className="mt-1 list-disc pl-5 text-gray-300">
                        {conceptGaps.map((item, i) => <li key={i}>{item}</li>)}
                    </ul>
                </div>
            )}

            {evaluation.follow_up_question && (
                <div>
                    <b>Follow-up:</b>
                    <p className="mt-1 text-gray-300">
                        {evaluation.follow_up_question}
                    </p>
                </div>
            )}

        </div>

    );

}
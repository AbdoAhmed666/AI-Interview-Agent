"use client";

import { useInterview } from "@/contexts/InterviewContext";

export default function ProgressBar(){

    const {

        questionNumber,
        totalQuestions,

    } = useInterview();

    const width=(questionNumber/totalQuestions)*100;

    return(

        <div className="w-full h-3 rounded-full bg-gray-700">

            <div
                className="h-3 rounded-full bg-blue-500 transition-all"
                style={{
                    width:`${width}%`
                }}
            />

        </div>

    );

}
"use client";

import { useEffect,useState } from "react";

import AppShell from "@/components/layout/AppShell";

import { getMySessions } from "@/services/history.service";

export default function DashboardPage(){

    const [sessions,setSessions]=useState<any[]>([]);

    useEffect(()=>{

        getMySessions().then(setSessions);

    },[]);

    const interviews=sessions.length;

    const scores=sessions
        .filter((x)=>x.overall_score!=null)
        .map((x)=>x.overall_score);

    const avg=scores.length
        ?(scores.reduce((a,b)=>a+b,0)/scores.length).toFixed(1)
        :"0";

    const best=scores.length
        ?Math.max(...scores)
        :"0";

    return(

        <AppShell>

            <h1 className="text-4xl font-bold mb-2">

                Welcome Back 👋

            </h1>

            <p className="text-gray-400 mb-8">

                Ready for your next AI interview?

            </p>

            <div className="grid md:grid-cols-2 xl:grid-cols-4 gap-6">

                <div className="rounded-xl bg-[var(--surface)] p-6">

                    <p>Interviews</p>

                    <h2 className="text-4xl font-bold">

                        {interviews}

                    </h2>

                </div>

                <div className="rounded-xl bg-[var(--surface)] p-6">

                    <p>Average Score</p>

                    <h2 className="text-4xl font-bold">

                        {avg}

                    </h2>

                </div>

                <div className="rounded-xl bg-[var(--surface)] p-6">

                    <p>Best Score</p>

                    <h2 className="text-4xl font-bold">

                        {best}

                    </h2>

                </div>

                <div className="rounded-xl bg-[var(--surface)] p-6">

                    <p>Completed</p>

                    <h2 className="text-4xl font-bold">

                        {
                            sessions.filter(
                                s=>s.status==="completed"
                            ).length
                        }

                    </h2>

                </div>

            </div>

        </AppShell>

    );

}
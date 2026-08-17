"use client";

import { useEffect, useState } from "react";

import AppShell from "@/components/layout/AppShell";

import { getMySessions } from "@/services/history.service";
import type { SessionSummary } from "@/types/interview";
import Link from "next/link";

export default function HistoryPage() {

    const [sessions, setSessions] = useState<SessionSummary[]>([]);

    useEffect(() => {
        getMySessions().then(setSessions);
    }, []);

    return (
        <AppShell>

            <h1 className="text-3xl font-bold mb-8">Interview History</h1>

            <div className="space-y-5">

                {sessions.length === 0 && (
                    <p className="text-gray-400">No interviews yet.</p>
                )}

                {sessions.map((session) => (
                    <div
                        key={session.id}
                        className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5"
                    >
                        <div className="flex justify-between">
                            <div>
                                <h3 className="font-bold">{session.role}</h3>
                                <p className="text-gray-400">{session.status}</p>
                            </div>

                            <div className="text-right">
                                <p>Score: {session.overallScore ?? "-"}</p>
                                <p>{session.recommendation ?? "-"}</p>
                                <div className="mt-2">
                                    <Link href={`/history/${session.id}`} className="text-sm underline">View</Link>
                                </div>
                            </div>
                        </div>
                    </div>
                ))}

            </div>

        </AppShell>
    );

}
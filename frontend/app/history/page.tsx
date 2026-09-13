"use client";

import { useEffect, useState } from "react";

import AppShell from "@/components/layout/AppShell";

import { getMySessions } from "@/services/history.service";
import type { SessionSummary } from "@/types/interview";
import Link from "next/link";
import { getApiErrorMessage } from "@/lib/apiError";

export default function HistoryPage() {

    const [sessions, setSessions] = useState<SessionSummary[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    useEffect(() => {
        let active = true;

        getMySessions()
            .then((data) => {
                if (active) setSessions(data);
            })
            .catch((err) => {
                if (active) setError(getApiErrorMessage(err));
            })
            .finally(() => {
                if (active) setLoading(false);
            });

        return () => {
            active = false;
        };
    }, []);

    return (
        <AppShell>

            <h1 className="text-3xl font-bold mb-8">Interview History</h1>

            <div className="space-y-5">

                {loading && <p className="text-gray-400">Loading…</p>}

                {error && (
                    <p className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                        {error}
                    </p>
                )}

                {!loading && !error && sessions.length === 0 && (
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
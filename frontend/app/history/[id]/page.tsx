"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import AppShell from "@/components/layout/AppShell";
import { getSession } from "@/services/history.service";
import type { SessionDetails } from "@/types/interview";

type SavedQuestion = { id?: number; question?: string; answer?: string | null; score?: number | null; feedback?: string | null; difficulty?: number | null };

export default function SessionPage() {
  const params = useParams<{ id?: string | string[] }>();
  const rawId = Array.isArray(params.id) ? params.id[0] : params.id;
  const sessionId = rawId && /^\d+$/.test(rawId) ? Number(rawId) : null;
  const [session, setSession] = useState<SessionDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!sessionId) { setError("Invalid interview ID."); setLoading(false); return; }
    let active = true;
    setLoading(true); setError(null);
    getSession(sessionId)
      .then((data) => { if (active) setSession(data); })
      .catch((err) => {
        if (!active) return;
        setError(err?.response?.status === 404 ? "Interview session not found." : "Unable to load this interview.");
      })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [sessionId]);

  if (loading) return <AppShell><p>Loading interview...</p></AppShell>;
  if (error) return <AppShell><p className="text-red-300">{error}</p><Link className="mt-4 inline-block underline" href="/history">Back to History</Link></AppShell>;
  if (!session) return <AppShell><p>No interview session found.</p><Link className="mt-4 inline-block underline" href="/history">Back to History</Link></AppShell>;

  const questions = (session.questions ?? []) as unknown as SavedQuestion[];
  return <AppShell><div className="space-y-4"><div className="flex flex-wrap items-center justify-between gap-3"><div><h1 className="text-2xl font-bold">Interview Report</h1><p className="text-gray-400">{session.role}</p></div><Link href="/history" className="underline">Back to History</Link></div><div className="rounded-xl border p-4 bg-[var(--surface)]"><p><strong>Score:</strong> {session.overallScore ?? "-"}</p><p><strong>Recommendation:</strong> {session.recommendation ?? "-"}</p><p><strong>Status:</strong> {session.status ?? "-"}</p></div><section className="space-y-3"><h2 className="text-xl font-bold">Questions &amp; Answers</h2>{questions.length ? questions.map((q,index)=><article className="rounded-xl border p-4 bg-[var(--surface)]" key={q.id ?? index}><p className="font-semibold">Question {index+1}: {q.question ?? "Question unavailable"}</p>{q.answer && <p className="mt-3"><strong>Answer:</strong> {q.answer}</p>}<div className="mt-3 flex flex-wrap gap-4 text-sm text-gray-300">{q.difficulty != null && <span>Difficulty: {q.difficulty}</span>}{q.score != null && <span>Score: {q.score}</span>}</div>{q.feedback && <p className="mt-3 text-gray-300"><strong>Feedback:</strong> {q.feedback}</p>}</article>):<p className="text-gray-400">No saved questions for this interview.</p>}</section></div></AppShell>;
}

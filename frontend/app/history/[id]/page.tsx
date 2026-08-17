"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";

import AppShell from "@/components/layout/AppShell";
import { getSession } from "@/services/history.service";
import api from "@/lib/axios";
import { downloadReport } from "@/services/report.service";
import type { SessionDetails } from "@/types/interview";

export default function SessionPage({ params }: { params: { id: string } }) {
  const { id } = params;
  const router = useRouter();

  const [session, setSession] = useState<SessionDetails | null>(null);
  const [summary, setSummary] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const sessionId = Number(id || 0);

  useEffect(() => {
    let mounted = true;
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await getSession(sessionId);
        if (!mounted) return;
        setSession(data);

        // call summarize-session to get the textual summary and strengths/weaknesses
        try {
          const resp = await api.post("/summarize-session", {
            role: data.role,
            questions: data.questions ?? [],
            answers: data.answers ?? [],
            evaluations: data.evaluations ?? [],
          });
          if (!mounted) return;
          setSummary(resp.data ?? resp);
        } catch (summErr) {
          // don't fail the whole page — show summary error
          console.warn("summarize-session failed", summErr);
        }
      } catch (err: any) {
        setError(err?.message ?? String(err));
      } finally {
        if (mounted) setLoading(false);
      }
    }

    load();
    return () => {
      mounted = false;
    };
  }, [sessionId]);

  async function handleDownload() {
    if (!session) return;

    const reportData = {
      role: session.role,
      overall_score: Math.round((summary?.overall_score ?? session.overallScore ?? 0) as number),
      overall_strengths: summary?.overall_strengths ?? [],
      overall_weaknesses: summary?.overall_weaknesses ?? [],
      hiring_recommendation: summary?.hiring_recommendation ?? session.recommendation ?? "",
      questions: session.questions ?? [],
      answers: session.answers ?? [],
      evaluations: session.evaluations ?? [],
    };

    try {
      await downloadReport(reportData);
    } catch (err) {
      // failing download should not crash page
      console.error("download failed", err);
    }
  }

  if (loading) {
    return (
      <AppShell>
        <p>Loading session...</p>
      </AppShell>
    );
  }

  if (error) {
    return (
      <AppShell>
        <p className="text-red-600">Error: {error}</p>
        <button onClick={() => router.push('/history')}>Back</button>
      </AppShell>
    );
  }

  if (!session) {
    return (
      <AppShell>
        <p>No session found.</p>
        <Link href="/history">Back to history</Link>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold">Session #{session.id}</h1>
          <div className="flex gap-2">
            <Link href="/history" className="btn">
              Back
            </Link>
            <button onClick={handleDownload} className="btn">
              Download Report
            </button>
          </div>
        </div>

        <div className="rounded-xl border p-4 bg-[var(--surface)]">
          <p><strong>Role:</strong> {session.role}</p>
          <p><strong>Score:</strong> {session.overallScore ?? "-"}</p>
          <p><strong>Recommendation:</strong> {session.recommendation ?? "-"}</p>
        </div>

        {summary && (
          <div className="rounded-xl border p-4 bg-[var(--surface)]">
            <h3 className="font-bold">Summary</h3>
            <pre className="whitespace-pre-wrap">{summary && (summary.overall_score !== undefined ? `Overall score: ${summary.overall_score}/10\nStrengths: ${summary.overall_strengths?.join(', ') ?? 'None'}\nWeaknesses: ${summary.overall_weaknesses?.join(', ') ?? 'None'}` : JSON.stringify(summary, null, 2))}</pre>
          </div>
        )}

        <div className="space-y-3">
          <h3 className="font-bold">Questions & Answers</h3>
          {(session.questions ?? []).map((q, idx) => (
            <div key={idx} className="rounded-md border p-3 bg-[var(--background)]">
              <p className="font-semibold">Q{idx + 1}: {q}</p>
              <p className="mt-2">A: {session.answers?.[idx] ?? "-"}</p>
              <details className="mt-2">
                <summary className="text-sm">Evaluation</summary>
                <pre className="whitespace-pre-wrap">{JSON.stringify(session.evaluations?.[idx] ?? {}, null, 2)}</pre>
              </details>
            </div>
          ))}
        </div>

      </div>
    </AppShell>
  );
}

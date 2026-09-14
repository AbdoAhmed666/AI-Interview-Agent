"use client";

import { useRouter } from "next/navigation";
import Button from "../ui/Button";
import { useInterview } from "@/contexts/InterviewContext";

export default function ResultPanel() {
  const router = useRouter();
  const { finished, overallScore, recommendation, reset } = useInterview();

  if (!finished) {
    return null;
  }

  return (
    <div className="rounded-2xl border border-[var(--border)] bg-[var(--surface)] p-6 space-y-5">
      <h3 className="text-xl font-bold">Interview Complete 🎉</h3>

      <div className="flex flex-wrap gap-8">
        <div>
          <div className="text-sm text-[var(--muted)]">Overall Score</div>
          <div className="text-3xl font-bold">
            {overallScore ?? "—"}
            <span className="text-lg font-normal text-[var(--muted)]">/10</span>
          </div>
        </div>

        <div>
          <div className="text-sm text-[var(--muted)]">Recommendation</div>
          <div className="text-2xl font-semibold">{recommendation || "—"}</div>
        </div>
      </div>

      <div className="flex flex-wrap gap-3 pt-1">
        <Button onClick={() => router.push("/history")}>View History</Button>
        <Button
          onClick={reset}
          className="bg-transparent border border-[var(--border)] hover:bg-[var(--surface)]"
        >
          New Interview
        </Button>
      </div>
    </div>
  );
}

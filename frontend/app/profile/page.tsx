"use client";

import AppLayout from "@/components/layout/AppLayout";
import CVUploader from "@/components/profile/CVUploader";
import { useEffect, useState } from "react";
import { getMyCV, getCVAnalysis } from "@/services/cv.service";

export default function ProfilePage() {
  const [cv, setCv] = useState<any>(null);

  const [analysis, setAnalysis] = useState<any>(null);

  async function refresh() {
    try {
      const c = await getMyCV();
      setCv(c);

      const a = await getCVAnalysis();
      setAnalysis(a);
    } catch (err) {
      console.error("Failed to fetch CV or analysis", err);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  return (
    <AppLayout>

      <h1 className="text-4xl font-bold mb-6">Profile</h1>

      <div className="max-w-2xl space-y-6">
        <CVUploader onUploaded={refresh} />

        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5">
          <h3 className="font-semibold">Uploaded CV</h3>
          <p className="text-sm text-[var(--muted)]">
            {cv?.active_cv ? cv.active_cv : "No active CV"}
          </p>

          {cv?.versions && cv.versions.length > 0 && (
            <div className="mt-3 text-sm">
              <strong>Versions:</strong>
              <ul className="list-disc list-inside">
                {cv.versions.map((v: string) => (
                  <li key={v}>{v}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5">
          <h3 className="font-semibold">CV Analysis</h3>
          <pre className="text-sm mt-2 max-h-64 overflow-auto">{JSON.stringify(analysis ?? { skills: [], frameworks: [], databases: [], projects: [] }, null, 2)}</pre>
        </div>

      </div>

    </AppLayout>
  );
}
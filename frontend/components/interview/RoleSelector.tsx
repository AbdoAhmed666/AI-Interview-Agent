"use client";

import axios from "axios";
import { useEffect, useState } from "react";
import Button from "../ui/Button";
import { useInterview } from "@/contexts/InterviewContext";
import { useAuth } from "@/contexts/AuthContext";
import { getMyCV, getCVAnalysis } from "@/services/cv.service";

const roles = [
  { value: "backend", label: "Backend Engineer" },
  { value: "frontend", label: "Frontend Engineer" },
  { value: "ml", label: "ML Engineer" },
  { value: "data_science", label: "Data Scientist" },
] as const;

function roleLabel(role: string) {
  return roles.find((option) => option.value === role)?.label ?? role;
}

function getApiErrorMessage(error: unknown) {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;

    if (typeof detail === "string") {
      return detail;
    }

    if (detail) {
      return JSON.stringify(detail);
    }

    return error.message;
  }

  return error instanceof Error ? error.message : "Unable to start the interview.";
}

export default function RoleSelector() {

  const [loading, setLoading] = useState(false);
  const [cv, setCv] = useState<any>(null);
  const [analysis, setAnalysis] = useState<any>(null);
  const [compatMessage, setCompatMessage] = useState<string | null>(null);
  const [compatScore, setCompatScore] = useState<number | null>(null);
  const [recommendedRoles, setRecommendedRoles] = useState<string[] | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [cvLoading, setCvLoading] = useState(true);

  const { isAuthenticated, loading: authLoading } = useAuth();

  const {
    role,
    setRole,
    start,
    loading: interviewLoading,
  } = useInterview();

  useEffect(() => {
    async function load() {
      try {
        const c = await getMyCV();
        setCv(c);

        const a = await getCVAnalysis();
        setAnalysis(a);
      } catch (err) {
        console.error("Failed to load CV or analysis", err);
        setErrorMessage(getApiErrorMessage(err));
      } finally {
        setCvLoading(false);
      }
    }

    load();
  }, []);

  async function handleStart() {

    if (!isAuthenticated || !cv?.active_cv || !analysis || !role) {
      return;
    }

    try {
      setLoading(true);
      setErrorMessage(null);

      const data = await start(role);

      // backend returns eligible flag when role incompatible
      if (data?.eligible === false) {
        setCompatMessage(data.message ?? "Role does not match CV.");
        setCompatScore(data.score ?? null);
        setRecommendedRoles(data.recommended_roles ?? null);
        return;
      }

      // clear previous compatibility info
      setCompatMessage(null);
      setCompatScore(null);
      setRecommendedRoles(null);

    } catch (error: unknown) {
      console.error(error);
      setErrorMessage(getApiErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  const canStart =
    isAuthenticated &&
    !authLoading &&
    !cvLoading &&
    Boolean(cv?.active_cv) &&
    Boolean(analysis) &&
    Boolean(role) &&
    !loading &&
    !interviewLoading;

  return (
    <div className="rounded-2xl bg-[var(--surface)] border border-[var(--border)] p-6">

      <h3 className="font-semibold mb-4">
        Choose Your Role
      </h3>

      <div className="mb-3 text-sm text-[var(--muted)]">
        {cvLoading
          ? "Checking your active CV..."
          : cv?.active_cv
            ? `Using CV: ${cv.active_cv}`
            : "Please upload your CV from your Profile."}
      </div>

      {!cvLoading && cv?.active_cv && !analysis && (
        <div className="mb-3 text-sm text-yellow-600">
          CV analysis is unavailable. Please re-upload your CV from Profile.
        </div>
      )}

      <div className="flex gap-4">

        <select
          value={role}
          onChange={(e) => setRole(e.target.value)}
          className="flex-1 rounded-xl bg-[var(--background)] border border-[var(--border)] p-3"
        >
          <option value="">Select Role</option>

          {roles.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}

        </select>

        <Button
          onClick={handleStart}
          disabled={!canStart}
          loading={loading || interviewLoading}
        >
          {loading || interviewLoading ? "Starting..." : "Start Interview"}
        </Button>

      </div>

      {compatMessage && (
        <div className="mt-4 rounded-md border border-yellow-200 bg-black p-3">
          <div className="font-semibold">Role compatibility</div>
          <div className="text-sm mt-1">{compatMessage}</div>
          {compatScore !== null && (
            <div className="text-sm mt-1">Match score: {compatScore}</div>
          )}
          {recommendedRoles && recommendedRoles.length > 0 && (
            <div className="text-sm mt-2">
              Recommended roles: {recommendedRoles.map(roleLabel).join(", ")}
            </div>
          )}
        </div>
      )}

      {errorMessage && (
        <div className="mt-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          {errorMessage}
        </div>
      )}

    </div>
  );
}

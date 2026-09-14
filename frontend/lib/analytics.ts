/**
 * Dashboard analytics, kept out of the page component so the numbers can be
 * tested directly.
 *
 * They were wrong for a long time in a way that was easy to miss: the page
 * compared `status === "completed"` against a database that stores
 * "COMPLETED", so finished interviews counted as zero while the very same page
 * listed them with their scores. Everything here goes through
 * `lib/sessionStatus` instead of comparing raw strings.
 */
import type { SessionSummary } from "@/types/interview";
import { isAbandonedSession, isCompletedSession } from "@/lib/sessionStatus";

export interface RoleAverage {
  role: string;
  avg: number;
}

export interface SessionAnalytics {
  /** Sessions that count towards the metrics (abandoned ones do not). */
  total: number;
  completed: SessionSummary[];
  /** Scores of completed interviews, newest first (as the API returns them). */
  scores: number[];
  average: number;
  best: number;
  /** Whole-percent share of counted sessions that were completed. */
  completionRate: number;
  /** Average score per role, strongest first. */
  roles: RoleAverage[];
}

export function summarizeSessions(
  sessions: SessionSummary[],
): SessionAnalytics {
  // An interview the candidate walked away from is not a failure to complete,
  // so it is left out of both sides of the completion rate.
  const counted = sessions.filter((s) => !isAbandonedSession(s.status));

  const completed = counted.filter(
    (s) => isCompletedSession(s.status) && s.overallScore != null,
  );

  const scores = completed.map((s) => s.overallScore as number);

  const average = scores.length
    ? scores.reduce((a, b) => a + b, 0) / scores.length
    : 0;

  const byRole = completed.reduce<Record<string, { sum: number; count: number }>>(
    (acc, session) => {
      const key = session.role;
      acc[key] ??= { sum: 0, count: 0 };
      acc[key].sum += session.overallScore as number;
      acc[key].count += 1;
      return acc;
    },
    {},
  );

  return {
    total: counted.length,
    completed,
    scores,
    average,
    best: scores.length ? Math.max(...scores) : 0,
    completionRate: counted.length
      ? Math.round((completed.length / counted.length) * 100)
      : 0,
    roles: Object.entries(byRole)
      .map(([role, v]) => ({ role, avg: v.sum / v.count }))
      .sort((a, b) => b.avg - a.avg),
  };
}

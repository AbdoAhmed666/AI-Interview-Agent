import { describe, expect, it } from "vitest";

import { summarizeSessions } from "@/lib/analytics";
import type { SessionSummary } from "@/types/interview";

function session(
  overrides: Partial<SessionSummary> & Pick<SessionSummary, "status">,
): SessionSummary {
  return {
    id: overrides.id ?? Math.floor(Math.random() * 1e6),
    role: overrides.role ?? "backend",
    status: overrides.status,
    overallScore: overrides.overallScore ?? null,
    recommendation: overrides.recommendation ?? null,
  };
}

describe("summarizeSessions", () => {
  it("counts completed interviews from the uppercase API status", () => {
    // The regression: with a lowercase comparison this returned zeros while
    // the same sessions were listed on screen with their scores.
    const analytics = summarizeSessions([
      session({ status: "COMPLETED", overallScore: 7, role: "ml" }),
      session({ status: "COMPLETED", overallScore: 6.6, role: "ml" }),
      session({ status: "IN_PROGRESS" }),
    ]);

    expect(analytics.completed).toHaveLength(2);
    expect(analytics.scores).toEqual([7, 6.6]);
    expect(analytics.average).toBeCloseTo(6.8);
    expect(analytics.best).toBe(7);
    expect(analytics.total).toBe(3);
    expect(analytics.completionRate).toBe(67);
  });

  it("leaves abandoned sessions out of the completion rate entirely", () => {
    const analytics = summarizeSessions([
      session({ status: "COMPLETED", overallScore: 8 }),
      session({ status: "ABANDONED" }),
      session({ status: "ABANDONED" }),
    ]);

    expect(analytics.total).toBe(1);
    expect(analytics.completionRate).toBe(100);
  });

  it("ignores a completed session that somehow has no score", () => {
    const analytics = summarizeSessions([
      session({ status: "COMPLETED", overallScore: null }),
    ]);

    expect(analytics.completed).toHaveLength(0);
    expect(analytics.scores).toEqual([]);
    expect(analytics.average).toBe(0);
    expect(analytics.best).toBe(0);
    expect(analytics.completionRate).toBe(0);
  });

  it("averages per role, strongest role first", () => {
    const analytics = summarizeSessions([
      session({ status: "COMPLETED", overallScore: 5, role: "backend" }),
      session({ status: "COMPLETED", overallScore: 7, role: "backend" }),
      session({ status: "COMPLETED", overallScore: 9, role: "ml" }),
    ]);

    expect(analytics.roles).toEqual([
      { role: "ml", avg: 9 },
      { role: "backend", avg: 6 },
    ]);
  });

  it("returns zeros for a candidate with no interviews", () => {
    const analytics = summarizeSessions([]);

    expect(analytics).toMatchObject({
      total: 0,
      scores: [],
      average: 0,
      best: 0,
      completionRate: 0,
      roles: [],
    });
  });
});

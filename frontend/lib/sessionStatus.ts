/**
 * Interview session status helpers.
 *
 * PostgreSQL is the authority for interview state and stores the status in
 * upper snake case (IN_PROGRESS, GENERATING, GENERATION_FAILED,
 * READY_TO_FINISH, COMPLETED), which `/my-sessions` and `/session/{id}` return
 * verbatim. Comparing those raw strings in the UI is what silently broke the
 * dashboard analytics: `status === "completed"` never matched "COMPLETED", so
 * every finished interview counted as zero. Normalize once, at the API
 * boundary, and compare against the constants below.
 */

export const SESSION_STATUS = {
  IN_PROGRESS: "IN_PROGRESS",
  GENERATING: "GENERATING",
  GENERATION_FAILED: "GENERATION_FAILED",
  READY_TO_FINISH: "READY_TO_FINISH",
  COMPLETED: "COMPLETED",
  // Left open when the candidate deliberately started a different interview.
  ABANDONED: "ABANDONED",
  UNKNOWN: "UNKNOWN",
} as const;

export type SessionStatus =
  (typeof SESSION_STATUS)[keyof typeof SESSION_STATUS];

const LABELS: Record<SessionStatus, string> = {
  IN_PROGRESS: "In progress",
  GENERATING: "Generating",
  GENERATION_FAILED: "Needs retry",
  READY_TO_FINISH: "Ready to finish",
  COMPLETED: "Completed",
  ABANDONED: "Abandoned",
  UNKNOWN: "Unknown",
};

/** Accepts any casing or separator the API might hand back. */
export function normalizeSessionStatus(raw: unknown): SessionStatus {
  const value = String(raw ?? "")
    .trim()
    .toUpperCase()
    .replace(/[\s-]+/g, "_");

  return value in LABELS ? (value as SessionStatus) : SESSION_STATUS.UNKNOWN;
}

/** True only for an interview that reached a final, scored state. */
export function isCompletedSession(raw: unknown): boolean {
  return normalizeSessionStatus(raw) === SESSION_STATUS.COMPLETED;
}

/** True for an interview nobody will ever finish; excluded from analytics. */
export function isAbandonedSession(raw: unknown): boolean {
  return normalizeSessionStatus(raw) === SESSION_STATUS.ABANDONED;
}

/** True while an interview can still be answered - i.e. it is resumable. */
export function isResumableSession(raw: unknown): boolean {
  const status = normalizeSessionStatus(raw);

  return (
    status === SESSION_STATUS.IN_PROGRESS ||
    status === SESSION_STATUS.GENERATING ||
    status === SESSION_STATUS.GENERATION_FAILED ||
    status === SESSION_STATUS.READY_TO_FINISH
  );
}

/** Human-readable label for a status chip. */
export function sessionStatusLabel(raw: unknown): string {
  return LABELS[normalizeSessionStatus(raw)];
}

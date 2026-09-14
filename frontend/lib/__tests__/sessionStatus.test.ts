import { describe, expect, it } from "vitest";

import {
  SESSION_STATUS,
  isAbandonedSession,
  isCompletedSession,
  isResumableSession,
  normalizeSessionStatus,
  sessionStatusLabel,
} from "@/lib/sessionStatus";

describe("normalizeSessionStatus", () => {
  it("passes through the upper snake case the API actually returns", () => {
    expect(normalizeSessionStatus("COMPLETED")).toBe(SESSION_STATUS.COMPLETED);
    expect(normalizeSessionStatus("IN_PROGRESS")).toBe(
      SESSION_STATUS.IN_PROGRESS,
    );
  });

  it("accepts other casings and separators", () => {
    expect(normalizeSessionStatus("completed")).toBe(SESSION_STATUS.COMPLETED);
    expect(normalizeSessionStatus(" in-progress ")).toBe(
      SESSION_STATUS.IN_PROGRESS,
    );
  });

  it("falls back to UNKNOWN rather than inventing a status", () => {
    expect(normalizeSessionStatus(null)).toBe(SESSION_STATUS.UNKNOWN);
    expect(normalizeSessionStatus(undefined)).toBe(SESSION_STATUS.UNKNOWN);
    expect(normalizeSessionStatus("")).toBe(SESSION_STATUS.UNKNOWN);
    expect(normalizeSessionStatus("something-else")).toBe(
      SESSION_STATUS.UNKNOWN,
    );
  });
});

describe("isCompletedSession", () => {
  // The original bug: the dashboard compared the raw API value against the
  // lowercase literal "completed", so nothing ever matched.
  it("recognizes the uppercase status the database stores", () => {
    expect(isCompletedSession("COMPLETED")).toBe(true);
  });

  it("is false for every non-final status", () => {
    expect(isCompletedSession("IN_PROGRESS")).toBe(false);
    expect(isCompletedSession("READY_TO_FINISH")).toBe(false);
    expect(isCompletedSession("ABANDONED")).toBe(false);
    expect(isCompletedSession(null)).toBe(false);
  });
});

describe("isAbandonedSession", () => {
  it("identifies only abandoned sessions", () => {
    expect(isAbandonedSession("ABANDONED")).toBe(true);
    expect(isAbandonedSession("IN_PROGRESS")).toBe(false);
    expect(isAbandonedSession("COMPLETED")).toBe(false);
  });
});

describe("isResumableSession", () => {
  it("covers every status the interview can still move on from", () => {
    expect(isResumableSession("IN_PROGRESS")).toBe(true);
    expect(isResumableSession("GENERATING")).toBe(true);
    expect(isResumableSession("GENERATION_FAILED")).toBe(true);
    expect(isResumableSession("READY_TO_FINISH")).toBe(true);
  });

  it("excludes the terminal ones", () => {
    expect(isResumableSession("COMPLETED")).toBe(false);
    expect(isResumableSession("ABANDONED")).toBe(false);
    expect(isResumableSession("UNKNOWN")).toBe(false);
  });
});

describe("sessionStatusLabel", () => {
  it("renders a human label instead of the database constant", () => {
    expect(sessionStatusLabel("COMPLETED")).toBe("Completed");
    expect(sessionStatusLabel("IN_PROGRESS")).toBe("In progress");
    expect(sessionStatusLabel("ABANDONED")).toBe("Abandoned");
    expect(sessionStatusLabel("GENERATION_FAILED")).toBe("Needs retry");
    expect(sessionStatusLabel("nonsense")).toBe("Unknown");
  });
});

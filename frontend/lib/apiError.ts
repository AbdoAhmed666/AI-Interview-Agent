import axios from "axios";

/**
 * Extract a user-facing message from an unknown error, understanding the
 * FastAPI `{ detail: ... }` error shape and axios network failures.
 */
export function getApiErrorMessage(
  error: unknown,
  fallback = "Something went wrong. Please try again."
): string {
  if (axios.isAxiosError(error)) {
    if (error.code === "ERR_NETWORK") {
      return "Cannot reach the server. Please check your connection.";
    }

    const detail = error.response?.data?.detail;
    if (typeof detail === "string") {
      return detail;
    }
    if (detail) {
      return JSON.stringify(detail);
    }

    return error.message || fallback;
  }

  return error instanceof Error ? error.message : fallback;
}

"use client";

import { useState } from "react";
import Button from "../ui/Button";
import { useInterview } from "@/contexts/InterviewContext";

export default function RoleSelector() {

  const [loading, setLoading] = useState(false);


  const {
    role,
    setRole,
    start,
} = useInterview();

async function handleStart() {

  if (!role) {
    alert("Please select a role.");
    return;
  }

  try {

    setLoading(true);

    await start(role);

  } catch (error) {

    console.error(error);

    alert("Failed to start interview.");

  } finally {

    setLoading(false);

  }
}
  return (
    <div className="rounded-2xl bg-[var(--surface)] border border-[var(--border)] p-6">

      <h3 className="font-semibold mb-4">
        Choose Your Role
      </h3>

      <div className="flex gap-4">

        <select
          value={role}
          onChange={(e) => setRole(e.target.value)}
          className="flex-1 rounded-xl bg-[var(--background)] border border-[var(--border)] p-3"
        >
          <option value="">Select Role</option>

          <option value="Backend Engineer">
            Backend Engineer
          </option>

          <option value="Frontend Engineer">
            Frontend Engineer
          </option>

          <option value="ML Engineer">
            ML Engineer
          </option>

          <option value="Data Scientist">
            Data Scientist
          </option>

        </select>

        <Button
          onClick={handleStart}
          disabled={loading}
        >
          {loading ? "Starting..." : "Start Interview"}
        </Button>

      </div>

    </div>
  );
}
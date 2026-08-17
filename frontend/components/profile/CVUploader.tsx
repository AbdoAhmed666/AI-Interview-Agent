"use client";

import { useState } from "react";
import api from "@/lib/axios";
import type { AxiosProgressEvent } from "axios";
import Button from "@/components/ui/Button";

export default function CVUploader({ onUploaded }: { onUploaded?: () => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState<number | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function handleUpload() {
    if (!file) {
      setMessage("Please select a file first.");
      return;
    }

    const form = new FormData();
    // backend expects field name `file`
    form.append("file", file);

    try {
      setLoading(true);
      setProgress(0);
      setMessage(null);

      const response = await api.post("/cv/upload", form, {
        headers: {
          // Let axios set the multipart boundary header automatically
        },
        onUploadProgress: (e?: AxiosProgressEvent) => {
          const loaded = e?.loaded;
          const total = e?.total;

          if (typeof loaded === "number" && typeof total === "number" && total > 0) {
            setProgress(Math.round((loaded / total) * 100));
          }
        },
      });

      // backend returns filename and analysis; show filename if available
      setMessage(response.data?.filename ? `Uploaded: ${response.data.filename}` : "Upload successful.");

      if (onUploaded) onUploaded();
    } catch (err: any) {
      console.error(err);
      const detail = err?.response?.data?.detail ?? err?.response?.data ?? err?.message;
      setMessage(String(detail) ?? "Upload failed.");
    } finally {
      setLoading(false);
      setProgress(null);
    }
  }

  return (
    <div className="rounded-2xl bg-[var(--surface)] border border-[var(--border)] p-6">
      <h3 className="font-semibold mb-4">Upload CV</h3>

      <div className="flex flex-col gap-3">
        <input
          type="file"
          accept=".pdf,application/pdf"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />

        <div className="flex items-center gap-3">
          <Button onClick={handleUpload} disabled={loading || !file}>
            {loading ? "Uploading..." : "Upload CV"}
          </Button>

          {progress !== null && (
            <div className="text-sm text-[var(--muted)]">{progress}%</div>
          )}
        </div>

        {file && (
          <div className="text-sm text-[var(--muted)]">Selected: {file.name}</div>
        )}

        {message && <div className="text-sm mt-2">{message}</div>}
      </div>
    </div>
  );
}

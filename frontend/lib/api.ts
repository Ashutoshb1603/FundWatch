import { ScanResult } from "./types";

const BASE_URL = (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");

type PresignResponse = {
  upload_id: string;
  keys: { previous: string; current: string };
  urls: { previous: string; current: string };
  max_bytes: number;
};

/** True when talking to the deployed API Gateway (real step reports); false for the local FastAPI server. */
export function isAwsMode() {
  // Explicit opt-in: any non-localhost URL (e.g. App Runner) still speaks the FastAPI /api protocol.
  return process.env.NEXT_PUBLIC_API_MODE === "aws";
}

async function jsonOrThrow(res: Response) {
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.error || body.detail || `Request failed (${res.status})`);
  return body;
}

export async function analyzeFactsheets(previous: File, current: File, schemeName?: string, onProgress?: (step: string) => void): Promise<ScanResult> {
  // AWS path: request presigned S3 URLs, upload PDFs directly to S3,
  // then start the asynchronous scan and poll until completion.
  if (isAwsMode()) {
    const presign = (await jsonOrThrow(await fetch(`${BASE_URL}/uploads/presign`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ files: { previous: previous.name, current: current.name } }),
    }))) as PresignResponse;

    if (previous.size > presign.max_bytes || current.size > presign.max_bytes) {
      throw new Error("Each PDF must be 25 MB or smaller.");
    }

    await Promise.all([
      uploadToS3(presign.urls.previous, previous),
      uploadToS3(presign.urls.current, current),
    ]);

    const started = (await jsonOrThrow(await fetch(`${BASE_URL}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        previous_key: presign.keys.previous,
        current_key: presign.keys.current,
        scheme_name: schemeName,
      }),
    }))) as { scan_id: string };

    return pollScan(started.scan_id, onProgress);
  }

  // Local development path remains direct multipart for simplicity.
  const form = new FormData();
  form.append("previous_factsheet", previous);
  form.append("current_factsheet", current);
  if (schemeName) form.append("scheme_name", schemeName);
  const res = await fetch(`${BASE_URL}/api/analyze`, { method: "POST", body: form });
  return jsonOrThrow(res) as Promise<ScanResult>;
}

async function uploadToS3(url: string, file: File) {
  const res = await fetch(url, {
    method: "PUT",
    headers: { "Content-Type": "application/pdf", "x-amz-server-side-encryption": "AES256" },
    body: file,
  });
  if (!res.ok) throw new Error(`S3 upload failed (${res.status})`);
}

async function pollScan(scanId: string, onProgress?: (step: string) => void): Promise<ScanResult> {
  for (let i = 0; i < 180; i += 1) {
    const res = await fetch(`${BASE_URL}/scans/${scanId}`, { cache: "no-store" });
    const scan = (await jsonOrThrow(res)) as ScanResult & { current_step?: string };
    if (scan.current_step) onProgress?.(scan.current_step);
    if (["completed", "validation_failed", "error"].includes(scan.status)) return scan;
    await new Promise((r) => setTimeout(r, 1000));
  }
  throw new Error("The scan is taking longer than expected. Please try again.");
}

export async function askAnalystChat(scanId: string, question: string) {
  // Local FastAPI serves under /api; the deployed API Gateway routes are unprefixed.
  const res = await fetch(`${BASE_URL}${isAwsMode() ? "" : "/api"}/scans/${scanId}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
  if (!res.ok) throw new Error(`Chat failed (${res.status})`);
  return res.json() as Promise<{ available: boolean; answer: string }>;
}

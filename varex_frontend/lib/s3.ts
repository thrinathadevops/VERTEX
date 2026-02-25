// lib/s3.ts — client-side S3 pre-signed upload helper

export type S3UploadType = "avatar" | "resume" | "badge" | "diagram";

export interface PresignedUploadResponse {
  upload_url:  string;   // PUT to this URL
  public_url:  string;   // final public URL after upload
  s3_key:      string;
}

/** Gets a pre-signed S3 URL from backend, then PUTs the file directly to S3 */
export async function uploadToS3(
  file:       File,
  uploadType: S3UploadType,
  onProgress?: (pct: number) => void
): Promise<PresignedUploadResponse> {
  // Step 1 — get pre-signed URL from backend
  const res = await fetch("/api/s3/presign", {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify({
      filename:    file.name,
      content_type: file.type,
      upload_type:  uploadType,
    }),
  });
  if (!res.ok) throw new Error("Failed to get upload URL");
  const { upload_url, public_url, s3_key }: PresignedUploadResponse = await res.json();

  // Step 2 — PUT file directly to S3 (no server in between = fast)
  await new Promise<void>((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("PUT", upload_url);
    xhr.setRequestHeader("Content-Type", file.type);
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    };
    xhr.onload  = () => (xhr.status === 200 ? resolve() : reject(new Error(`S3 upload failed: ${xhr.status}`)));
    xhr.onerror = () => reject(new Error("S3 upload network error"));
    xhr.send(file);
  });

  return { upload_url, public_url, s3_key };
}

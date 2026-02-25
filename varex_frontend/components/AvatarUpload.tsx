// PATH: components/AvatarUpload.tsx
"use client";

import { useRef, useState } from "react";
import { uploadToS3 } from "@/lib/s3";

interface AvatarUploadProps {
  currentUrl?: string;
  name:        string;
  onUpload:    (publicUrl: string, s3Key: string) => void;
}

export default function AvatarUpload({ currentUrl, name, onUpload }: AvatarUploadProps) {
  const inputRef               = useRef<HTMLInputElement>(null);
  const [preview,  setPreview] = useState<string | null>(currentUrl ?? null);
  const [progress, setProgress]= useState<number>(0);
  const [uploading,setUploading]= useState(false);
  const [error,    setError]   = useState<string | null>(null);

  const initials = name
    .split(" ")
    .map((w) => w[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  const handleFile = async (file: File) => {
    if (!file.type.match(/^image\/(jpeg|png|webp)$/)) {
      setError("Only JPEG, PNG, or WEBP images are allowed.");
      return;
    }
    if (file.size > 2 * 1024 * 1024) {
      setError("File must be under 2 MB.");
      return;
    }

    setError(null);
    setUploading(true);
    setProgress(0);

    // Show local preview immediately
    const reader = new FileReader();
    reader.onload = (e) => setPreview(e.target?.result as string);
    reader.readAsDataURL(file);

    try {
      const { public_url, s3_key } = await uploadToS3(file, "avatar", setProgress);
      onUpload(public_url, s3_key);
    } catch (err: any) {
      setError(err.message ?? "Upload failed. Try again.");
      setPreview(currentUrl ?? null);
    } finally {
      setUploading(false);
      setProgress(0);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  return (
    <div className="flex flex-col items-center gap-3">
      {/* Avatar circle */}
      <div
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        className="relative h-20 w-20 rounded-full cursor-pointer
          ring-2 ring-slate-700 hover:ring-sky-500 transition overflow-hidden group"
      >
        {preview ? (
          <img src={preview} alt={name} className="h-full w-full object-cover" />
        ) : (
          <div className="flex h-full w-full items-center justify-center
            bg-sky-500/20 text-sky-300 text-xl font-bold">
            {initials}
          </div>
        )}

        {/* Hover overlay */}
        <div className="absolute inset-0 flex flex-col items-center justify-center
          bg-black/60 opacity-0 group-hover:opacity-100 transition rounded-full">
          <svg className="h-5 w-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          <span className="text-[10px] text-white mt-1">Change</span>
        </div>

        {/* Upload progress ring */}
        {uploading && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/50 rounded-full">
            <div className="relative h-10 w-10">
              <svg className="h-10 w-10 -rotate-90" viewBox="0 0 36 36">
                <circle cx="18" cy="18" r="15.9155" fill="none"
                  stroke="#334155" strokeWidth="2.5" />
                <circle cx="18" cy="18" r="15.9155" fill="none"
                  stroke="#0ea5e9" strokeWidth="2.5"
                  strokeDasharray={`${progress}, 100`}
                  strokeLinecap="round" />
              </svg>
              <span className="absolute inset-0 flex items-center justify-center
                text-[10px] text-white font-medium">
                {progress}%
              </span>
            </div>
          </div>
        )}
      </div>

      <input
        ref={inputRef}
        type="file"
        accept="image/jpeg,image/png,image/webp"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0];
          if (file) handleFile(file);
          e.target.value = "";
        }}
      />

      <p className="text-[11px] text-slate-400 text-center">
        Click or drag an image · JPEG / PNG / WEBP · max 2 MB
      </p>

      {error && (
        <p className="text-[11px] text-red-400 text-center">{error}</p>
      )}
    </div>
  );
}

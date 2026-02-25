// PATH: varex_frontend/app/api/s3/presign/route.ts
// FIX: Bug 4.2 — This route was called by lib/s3.ts but didn't exist

import { NextRequest, NextResponse } from "next/server";
import {
  S3Client,
  PutObjectCommand,
} from "@aws-sdk/client-s3";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner";
import { v4 as uuidv4 } from "uuid";

const s3 = new S3Client({
  region:      process.env.AWS_REGION!,
  credentials: {
    accessKeyId:     process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
  },
});

const ALLOWED_TYPES: Record<string, string> = {
  "image/jpeg": "jpg",
  "image/png":  "png",
  "image/webp": "webp",
  "application/pdf": "pdf",
};

export async function POST(req: NextRequest) {
  try {
    const { file_type, upload_type = "avatar" } = await req.json();

    const ext = ALLOWED_TYPES[file_type];
    if (!ext) {
      return NextResponse.json({ detail: "File type not allowed" }, { status: 400 });
    }

    const key        = `${upload_type}/${uuidv4()}.${ext}`;
    const bucket     = process.env.AWS_S3_BUCKET!;
    const cdnBase    = process.env.AWS_CLOUDFRONT_URL ?? `https://${bucket}.s3.amazonaws.com`;
    const public_url = `${cdnBase}/${key}`;

    const command = new PutObjectCommand({
      Bucket:      bucket,
      Key:         key,
      ContentType: file_type,
    });

    const upload_url = await getSignedUrl(s3, command, { expiresIn: 300 }); // 5 min

    return NextResponse.json({ upload_url, public_url, s3_key: key });
  } catch (err) {
    console.error("S3 presign error:", err);
    return NextResponse.json({ detail: "Failed to generate upload URL" }, { status: 500 });
  }
}

// PATH: app/api/s3/presign/route.ts
import { NextRequest, NextResponse } from "next/server";
import { S3Client, PutObjectCommand } from "@aws-sdk/client-s3";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner";
import { cookies } from "next/headers";
import { v4 as uuidv4 } from "uuid";

const s3 = new S3Client({
  region: process.env.AWS_REGION ?? "ap-south-1",
  credentials: {
    accessKeyId:     process.env.AWS_ACCESS_KEY_ID     ?? "",
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY ?? "",
  },
});

const BUCKET   = process.env.AWS_S3_BUCKET        ?? "varex-assets";
const CDN_BASE = process.env.AWS_CLOUDFRONT_URL   ?? `https://${BUCKET}.s3.ap-south-1.amazonaws.com`;

const ALLOWED_TYPES: Record<string, string[]> = {
  avatar:  ["image/jpeg", "image/png", "image/webp"],
  resume:  ["application/pdf"],
  badge:   ["image/jpeg", "image/png", "image/svg+xml"],
  diagram: ["image/png", "image/jpeg", "image/svg+xml", "application/pdf"],
};

export async function POST(req: NextRequest) {
  const cookieStore = await cookies();
  const token = cookieStore.get("access_token")?.value;
  if (!token) return NextResponse.json({ error: "Unauthorized" }, { status: 401 });

  const { filename, content_type, upload_type } = await req.json();

  const allowed = ALLOWED_TYPES[upload_type];
  if (!allowed?.includes(content_type)) {
    return NextResponse.json({ error: "File type not allowed" }, { status: 400 });
  }

  const ext    = filename.split(".").pop();
  const s3Key  = `${upload_type}/${uuidv4()}.${ext}`;

  const command = new PutObjectCommand({
    Bucket:      BUCKET,
    Key:         s3Key,
    ContentType: content_type,
  });

  const upload_url = await getSignedUrl(s3, command, { expiresIn: 300 });
  const public_url = `${CDN_BASE}/${s3Key}`;

  return NextResponse.json({ upload_url, public_url, s3_key: s3Key });
}

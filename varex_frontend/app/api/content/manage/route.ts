import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";

// Handles destructive/management actions like Delete Post and Create Category
const CONTENT_DIR = path.join(process.cwd(), "content", "blog");

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { action, payload } = body;

    if (!action) {
      return NextResponse.json({ error: "Missing action parameter" }, { status: 400 });
    }

    // ─────────────────────────────────────────────────────────────────
    // ACTION: DELETE POST
    // ─────────────────────────────────────────────────────────────────
    if (action === "delete") {
      const { category, slug } = payload;
      if (!category || !slug) {
        return NextResponse.json({ error: "Missing category or slug for deletion" }, { status: 400 });
      }

      const filePath = path.join(CONTENT_DIR, category, `${slug}.md`);

      // Verify file exists before deleting
      if (fs.existsSync(filePath)) {
        fs.unlinkSync(filePath); // Physically delete the file
        return NextResponse.json({ success: true, message: "File deleted successfully" }, { status: 200 });
      } else {
        return NextResponse.json({ error: "File not found" }, { status: 404 });
      }
    }

    // ─────────────────────────────────────────────────────────────────
    // ACTION: CREATE CATEGORY
    // ─────────────────────────────────────────────────────────────────
    if (action === "create_category") {
      const { new_category } = payload;
      if (!new_category) {
        return NextResponse.json({ error: "Missing new_category name" }, { status: 400 });
      }

      // Format category name for filesystem (lowercase, snake_case)
      const formattedCategory = new_category
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "_")
        .replace(/(^_|_$)+/g, "");

      const dirPath = path.join(CONTENT_DIR, formattedCategory);
      
      if (!fs.existsSync(dirPath)) {
        fs.mkdirSync(dirPath, { recursive: true });
        return NextResponse.json({ success: true, category: formattedCategory, message: "Folder created successfully" }, { status: 201 });
      } else {
        return NextResponse.json({ error: "Category folder already exists" }, { status: 409 });
      }
    }

    // ─────────────────────────────────────────────────────────────────
    // ACTION: UNKNOWN
    // ─────────────────────────────────────────────────────────────────
    return NextResponse.json({ error: "Unknown action provided" }, { status: 400 });

  } catch (error) {
    console.error("Local Content Manage Error:", error);
    return NextResponse.json({ error: "Fatal error executing management command" }, { status: 500 });
  }
}

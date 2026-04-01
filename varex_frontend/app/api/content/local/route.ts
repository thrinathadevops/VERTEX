import { NextResponse } from "next/server";
import fs from "fs";
import path from "path";
import matter from "gray-matter";
import { marked } from "marked";

// Next.js App Router API Route for managing local Markdown blogs
// Handles both Reading (GET) and Writing (POST)

const CONTENT_DIR = path.join(process.cwd(), "content", "blog");

export async function GET() {
  try {
    const categories = ["devops", "sap", "security", "architecture", "ai_hiring", "aws_interview"];
    const allPosts: any[] = [];

    // Recursively read all folders
    for (const cat of categories) {
      const dirPath = path.join(CONTENT_DIR, cat);
      if (fs.existsSync(dirPath)) {
        const files = fs.readdirSync(dirPath);
        for (const file of files) {
          if (file.endsWith(".md")) {
            const rawContent = fs.readFileSync(path.join(dirPath, file), "utf-8");
            const { data, content } = matter(rawContent);

            // Map it to our internal ContentItem schema
            allPosts.push({
              id: `local-${cat}-${file}`,
              title: data.title || "Untitled",
              slug: file.replace(".md", ""),
              body: await marked.parse(content),
              category: data.category || cat,
              access_level: data.access_level || "free",
              is_published: true,
              author_id: data.author || "system",
              created_at: data.date || new Date().toISOString()
            });
          }
        }
      }
    }

    // Sort by date descending
    allPosts.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

    return NextResponse.json(allPosts, { status: 200 });
  } catch (error) {
    console.error("Local Content Parser Error:", error);
    return NextResponse.json({ error: "Failed to parse local content" }, { status: 500 });
  }
}

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { title, category, content } = body;

    if (!title || !category || !content) {
      return NextResponse.json({ error: "Missing required fields" }, { status: 400 });
    }

    // Create a slug from the title
    const slug = title
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/(^-|-$)+/g, "");

    const dirPath = path.join(CONTENT_DIR, category);
    
    // Ensure directory exists
    if (!fs.existsSync(dirPath)) {
      fs.mkdirSync(dirPath, { recursive: true });
    }

    const filePath = path.join(dirPath, `${slug}.md`);

    // Create Markdown Frontmatter
    const mdContent = `---
title: "${title}"
category: "${category}"
date: "${new Date().toISOString()}"
author: "Admin"
---

${content}`;

    // Physically write the file to the user's hard drive
    fs.writeFileSync(filePath, mdContent, "utf-8");

    return NextResponse.json({ success: true, slug }, { status: 201 });
  } catch (error) {
    console.error("Local Content Write Error:", error);
    return NextResponse.json({ error: "Failed to write local content file" }, { status: 500 });
  }
}

"use client";

import { useState } from "react";
import { Lock, FileText, CheckCircle2, AlertCircle, Plus, LayoutDashboard, Send } from "lucide-react";
import AnimateIn from "@/components/AnimateIn";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function AdminDashboardPage() {
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  
  // Login State
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loginError, setLoginError] = useState(false);

  // Editor State
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("devops");
  const [content, setContent] = useState("");
  
  // Submission State
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (username === "admin" && password === "admin") {
      setIsAuthenticated(true);
      setLoginError(false);
    } else {
      setLoginError(true);
    }
  };

  const handlePublish = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMsg("");
    setSuccessMsg("");

    try {
      const res = await fetch("/api/content/local", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, category, content }),
      });

      if (!res.ok) {
        throw new Error("Failed to publish to filesystem");
      }

      const data = await res.json();
      setSuccessMsg(`Successfully published! Created: ${data.slug}.md`);
      setTitle("");
      setContent("");
      
      // Auto redirect to blog after 2 seconds
      setTimeout(() => {
        router.push("/blog");
      }, 2000);

    } catch (err) {
      setErrorMsg("Failed to generate file. Check server logs.");
    } finally {
      setIsSubmitting(false);
    }
  };

  // ── Authentication Wall ───────────────────────────────────────────
  if (!isAuthenticated) {
    return (
      <div className="min-h-[70vh] flex items-center justify-center p-4">
        <AnimateIn className="w-full max-w-md">
          <div className="bg-slate-900/50 border border-slate-800 p-8 rounded-2xl shadow-2xl backdrop-blur-xl">
            <div className="flex justify-center mb-6">
              <div className="p-4 bg-sky-500/10 rounded-full">
                <Lock className="w-8 h-8 text-sky-400" />
              </div>
            </div>
            <h1 className="text-2xl font-bold text-center text-white mb-2">Admin Portal</h1>
            <p className="text-sm text-slate-400 text-center mb-8">Sign in to manage VAREX content</p>
            
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Username</label>
                <input 
                  type="text" 
                  value={username} onChange={(e) => setUsername(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-sky-500 transition-colors"
                  placeholder="admin"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Password</label>
                <input 
                  type="password" 
                  value={password} onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-sky-500 transition-colors"
                  placeholder="••••••••"
                />
              </div>

              {loginError && (
                <div className="flex items-center gap-2 text-red-400 bg-red-400/10 p-3 rounded-lg text-xs font-medium">
                  <AlertCircle className="w-4 h-4" /> Invalid credentials.
                </div>
              )}

              <button type="submit" className="w-full bg-sky-500 hover:bg-sky-400 text-white font-bold py-2.5 rounded-lg transition-colors mt-4">
                Authenticate
              </button>
            </form>
          </div>
        </AnimateIn>
      </div>
    );
  }

  // ── Dashboard / CMS Writer ─────────────────────────────────────────
  return (
    <div className="max-w-5xl mx-auto pb-20">
      <header className="mb-8 flex items-end justify-between border-b border-slate-800 pb-5">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-3">
            <LayoutDashboard className="text-sky-400 w-6 h-6" /> 
            Admin CMS
          </h1>
          <p className="text-sm text-slate-400 mt-2">Create new native Markdown blogs.</p>
        </div>
        <Link href="/blog" className="text-sm font-medium text-sky-400 hover:text-sky-300">
          View Live Blog →
        </Link>
      </header>

      <div className="grid lg:grid-cols-3 gap-8">
        
        {/* Left: Sidebar */}
        <div className="lg:col-span-1 space-y-4">
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5">
            <h3 className="font-semibold text-white mb-4 flex items-center gap-2">
              <Plus className="w-4 h-4 text-emerald-400" /> Quick Actions
            </h3>
            <button className="w-full text-left px-4 py-2.5 rounded-lg bg-sky-500/10 text-sky-400 font-medium text-sm border border-sky-500/20">
              ✍️ Write New Post
            </button>
            <button className="w-full text-left px-4 py-2.5 rounded-lg hover:bg-slate-800 text-slate-300 font-medium text-sm transition-colors mt-2">
              📁 Manage Categories
            </button>
          </div>
        </div>

        {/* Right: Editor */}
        <div className="lg:col-span-2">
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 lg:p-8">
            <h2 className="text-lg font-bold text-white mb-6 flex items-center gap-2">
              <FileText className="w-5 h-5 text-slate-400" />
              Compose New Article
            </h2>

            {successMsg && (
              <div className="mb-6 flex items-center justify-between gap-3 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 p-4 rounded-xl text-sm font-medium animate-in fade-in slide-in-from-top-4">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5" />
                  {successMsg}
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 rounded-full border-2 border-emerald-500 border-t-transparent animate-spin" />
                  <span className="text-xs">Redirecting...</span>
                </div>
              </div>
            )}

            {errorMsg && (
              <div className="mb-6 flex items-center gap-2 bg-red-500/10 border border-red-500/30 text-red-400 p-4 rounded-xl text-sm font-medium">
                <AlertCircle className="w-5 h-5" />
                {errorMsg}
              </div>
            )}

            <form onSubmit={handlePublish} className="space-y-5">
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                <div className="space-y-1.5 sm:col-span-2">
                  <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Post Title</label>
                  <input 
                    type="text" 
                    required
                    value={title} onChange={(e) => setTitle(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-sky-500 transition-colors"
                    placeholder="e.g. 5 Zero-Trust Architecture Secrets..."
                  />
                </div>

                <div className="space-y-1.5 sm:col-span-2">
                  <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Category Routing</label>
                  <select 
                    value={category} onChange={(e) => setCategory(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-sky-500 transition-colors appearance-none"
                  >
                    <option value="devops">DevOps & CI/CD</option>
                    <option value="sap">SAP SD</option>
                    <option value="security">Cybersecurity</option>
                    <option value="architecture">Software Architecture</option>
                    <option value="ai_hiring">AI Hiring Systems</option>
                  </select>
                </div>
              </div>

              <div className="space-y-1.5 border-t border-slate-800 pt-5 mt-5">
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Markdown Content</label>
                  <span className="text-[10px] text-slate-500 font-mono">Supports GitHub Flavored Markdown</span>
                </div>
                <textarea 
                  required
                  value={content} onChange={(e) => setContent(e.target.value)}
                  rows={14}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-4 text-slate-300 font-mono text-sm focus:outline-none focus:border-sky-500 transition-colors leading-relaxed"
                  placeholder="## Introduction..."
                />
              </div>

              <div className="pt-4 flex justify-end">
                <button 
                  type="submit" 
                  disabled={isSubmitting}
                  className="inline-flex items-center gap-2 bg-sky-500 hover:bg-sky-400 disabled:opacity-50 text-white font-bold py-3 px-8 rounded-xl transition-all shadow-lg hover:shadow-sky-500/20"
                >
                  {isSubmitting ? "Generating File..." : "Publish to Filesystem"} 
                  {!isSubmitting && <Send className="w-4 h-4 ml-1" />}
                </button>
              </div>

            </form>
          </div>
        </div>

      </div>
    </div>
  );
}

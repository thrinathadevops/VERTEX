"use client";

import { useState, useEffect } from "react";
import { Lock, FileText, CheckCircle2, AlertCircle, Plus, LayoutDashboard, Send, Trash2, FolderPlus, RefreshCw, Edit } from "lucide-react";
import AnimateIn from "@/components/AnimateIn";
import Link from "next/link";
import { useRouter } from "next/navigation";

type ContentItem = any; // simplified for dashboard
type TabType = "write" | "manage" | "categories";

export default function AdminDashboardPage() {
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [activeTab, setActiveTab] = useState<TabType>("write");
  
  // Login State
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loginError, setLoginError] = useState(false);

  // Editor State
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState("devops");
  const [content, setContent] = useState("");
  
  // Management State
  const [posts, setPosts] = useState<ContentItem[]>([]);
  const [loadingPosts, setLoadingPosts] = useState(false);
  const [newCatName, setNewCatName] = useState("");

  // Submission State
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");
  const [errorMsg, setErrorMsg] = useState("");

  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (username === "admin" && password === "admin") {
      setIsAuthenticated(true);
      setLoginError(false);
      fetchPosts();
    } else {
      setLoginError(true);
    }
  };

  const fetchPosts = async () => {
    setLoadingPosts(true);
    try {
      const res = await fetch("/api/content/local");
      if (res.ok) {
        setPosts(await res.json());
      }
    } catch(e) {
      console.error(e);
    } finally {
      setLoadingPosts(false);
    }
  };

  const handlePublish = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMsg(""); setSuccessMsg("");

    try {
      const res = await fetch("/api/content/local", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, category, content }),
      });
      if (!res.ok) throw new Error("Failed to publish");
      
      const data = await res.json();
      setSuccessMsg(`Published! Overwrote: ${data.slug}.md`);
      fetchPosts();
      setTimeout(() => setSuccessMsg(""), 3000);
    } catch (err) {
      setErrorMsg("Failed to generate file.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (cat: string, slug: string) => {
    if (!confirm(`Are you sure you want to permanently delete the markdown file for "${slug}"?`)) return;
    
    try {
      const res = await fetch("/api/content/manage", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "delete", payload: { category: cat, slug } }),
      });
      if (!res.ok) throw new Error("Delete failed");
      
      fetchPosts(); // Refresh list
    } catch(err) {
      alert("Error deleting file natively.");
    }
  };

  const handleCreateCategory = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCatName) return;
    setIsSubmitting(true);
    setErrorMsg(""); setSuccessMsg("");

    try {
      const res = await fetch("/api/content/manage", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "create_category", payload: { new_category: newCatName } }),
      });
      if (!res.ok) throw new Error("Directory creation failed (might already exist)");
      
      const data = await res.json();
      setSuccessMsg(`Folder 'content/blog/${data.category}' created!`);
      setNewCatName("");
      setTimeout(() => setSuccessMsg(""), 3000);
    } catch (err) {
      setErrorMsg("Directory creation failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const loadIntoEditor = (post: ContentItem) => {
    setTitle(post.title);
    setCategory(post.category);
    // Since body is parsed HTML from GET, editing existing posts directly requires the raw MD.
    // For this CMS V1, we stringify it back or just tell them to overwrite.
    setContent(post.body.replace(/<[^>]+>/g, "").substring(0, 100) + "... [RAW MARKDOWN NEEDED TO EDIT - NOT SUPPORTED YET]");
    setActiveTab("write");
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
                  type="text" value={username} onChange={(e) => setUsername(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-sky-500 transition-colors" placeholder="admin"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Password</label>
                <input 
                  type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-white focus:outline-none focus:border-sky-500 transition-colors" placeholder="••••••••"
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
            <LayoutDashboard className="text-sky-400 w-6 h-6" /> Admin CMS
          </h1>
          <p className="text-sm text-slate-400 mt-2">Manage native Markdown files strictly from the UI.</p>
        </div>
        <Link href="/blog" className="text-sm font-medium text-sky-400 hover:text-sky-300">
          View Live Blog →
        </Link>
      </header>

      <div className="grid lg:grid-cols-4 gap-8">
        
        {/* Left: Sidebar Tabs */}
        <div className="lg:col-span-1 space-y-4">
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-3 flex flex-col gap-1">
            <button 
              onClick={() => setActiveTab("write")}
              className={`w-full text-left px-4 py-2.5 rounded-lg font-medium text-sm border transition-all flex items-center gap-2
                ${activeTab === "write" ? "bg-sky-500/10 text-sky-400 border-sky-500/20" : "bg-transparent text-slate-400 border-transparent hover:bg-slate-800"}`}
            >
              <FileText className="w-4 h-4" /> Write Post
            </button>
            <button 
              onClick={() => { setActiveTab("manage"); fetchPosts(); }}
              className={`w-full text-left px-4 py-2.5 rounded-lg font-medium text-sm border transition-all flex items-center gap-2
                ${activeTab === "manage" ? "bg-sky-500/10 text-sky-400 border-sky-500/20" : "bg-transparent text-slate-400 border-transparent hover:bg-slate-800"}`}
            >
              <LayoutDashboard className="w-4 h-4" /> Manage Posts
            </button>
            <button 
              onClick={() => setActiveTab("categories")}
              className={`w-full text-left px-4 py-2.5 rounded-lg font-medium text-sm border transition-all flex items-center gap-2
                ${activeTab === "categories" ? "bg-sky-500/10 text-sky-400 border-sky-500/20" : "bg-transparent text-slate-400 border-transparent hover:bg-slate-800"}`}
            >
              <FolderPlus className="w-4 h-4" /> Manage Categories
            </button>
          </div>
        </div>

        {/* Right: Active Tab Content */}
        <div className="lg:col-span-3">
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 lg:p-8 min-h-[500px]">
            
            {/* Global Messages */}
            {successMsg && (
              <div className="mb-6 flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 p-4 rounded-xl text-sm font-medium animate-in fade-in slide-in-from-top-4">
                <CheckCircle2 className="w-5 h-5 flex-shrink-0" /> {successMsg}
              </div>
            )}
            {errorMsg && (
              <div className="mb-6 flex items-center gap-2 bg-red-500/10 border border-red-500/30 text-red-400 p-4 rounded-xl text-sm font-medium">
                <AlertCircle className="w-5 h-5 flex-shrink-0" /> {errorMsg}
              </div>
            )}

            {/* TAB: WRITE POST */}
            {activeTab === "write" && (
              <form onSubmit={handlePublish} className="space-y-5 animate-in fade-in">
                <h2 className="text-lg font-bold text-white mb-6 border-b border-slate-800 pb-3">Compose New Article</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                  <div className="space-y-1.5 sm:col-span-2">
                    <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Post Title</label>
                    <input 
                      type="text" required value={title} onChange={(e) => setTitle(e.target.value)}
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
                      {/* Note: Dynamic categories would require reading the dir list */}
                    </select>
                  </div>
                </div>
                <div className="space-y-1.5 border-t border-slate-800 pt-5 mt-5">
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">Markdown Content</label>
                  </div>
                  <textarea 
                    required value={content} onChange={(e) => setContent(e.target.value)} rows={14}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-4 text-slate-300 font-mono text-sm focus:outline-none focus:border-sky-500 transition-colors leading-relaxed"
                    placeholder="## Introduction..."
                  />
                </div>
                <div className="pt-4 flex justify-end">
                  <button type="submit" disabled={isSubmitting} className="inline-flex items-center gap-2 bg-sky-500 hover:bg-sky-400 disabled:opacity-50 text-white font-bold py-3 px-8 rounded-xl transition-all shadow-lg">
                    {isSubmitting ? "Generating File..." : "Publish to Filesystem"} <Send className="w-4 h-4 ml-1" />
                  </button>
                </div>
              </form>
            )}

            {/* TAB: MANAGE POSTS */}
            {activeTab === "manage" && (
              <div className="animate-in fade-in">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-6">
                  <h2 className="text-lg font-bold text-white">Manage Written Posts</h2>
                  <button onClick={fetchPosts} className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg transition-colors text-slate-300" title="Refresh local files">
                    <RefreshCw className={`w-4 h-4 ${loadingPosts ? "animate-spin" : ""}`} />
                  </button>
                </div>
                
                {posts.length === 0 && !loadingPosts && (
                  <p className="text-sm text-slate-400 py-10 text-center">No markdown files found in the content directory.</p>
                )}

                <div className="space-y-3">
                  {posts.map((post) => (
                    <div key={post.id} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-xl border border-slate-800 bg-slate-950/50 hover:border-sky-500/30 transition-colors">
                      <div>
                        <h3 className="text-sm font-semibold text-white truncate max-w-sm">{post.title}</h3>
                        <div className="flex gap-2 text-xs text-slate-500 mt-1">
                          <span className="bg-slate-800 px-2 py-0.5 rounded text-sky-400 uppercase text-[9px] font-bold">{post.category}</span>
                          <span>{post.slug}.md</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <button 
                          onClick={() => loadIntoEditor(post)}
                          className="p-2 text-slate-400 hover:text-emerald-400 hover:bg-emerald-400/10 rounded-lg transition-colors border border-transparent hover:border-emerald-400/20"
                          title="Overwrite Post"
                        >
                          <Edit className="w-4 h-4" />
                        </button>
                        <button 
                          onClick={() => handleDelete(post.category, post.slug)}
                          className="p-2 text-slate-400 hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-colors border border-transparent hover:border-red-400/20"
                          title="Physically Delete File"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* TAB: CATEGORIES */}
            {activeTab === "categories" && (
              <div className="animate-in fade-in max-w-lg">
                <h2 className="text-lg font-bold text-white border-b border-slate-800 pb-3 mb-6">Category Builder</h2>
                <p className="text-sm text-slate-400 mb-6">Creates a new physical folder in <code className="text-sky-400">content/blog/</code> to store upcoming posts.</p>
                
                <form onSubmit={handleCreateCategory} className="space-y-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-bold text-slate-400 uppercase tracking-wider">New Category Name</label>
                    <input 
                      type="text" required value={newCatName} onChange={(e) => setNewCatName(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-sky-500 transition-colors"
                      placeholder="e.g. Cloud Computing"
                    />
                  </div>
                  <button type="submit" disabled={isSubmitting} className="w-full inline-flex justify-center items-center gap-2 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-white font-bold py-3 px-8 rounded-xl transition-all border border-slate-700 hover:border-slate-500">
                    {isSubmitting ? "Building directory..." : "Generate OS Folder"} <FolderPlus className="w-4 h-4" />
                  </button>
                </form>
              </div>
            )}

          </div>
        </div>
      </div>
    </div>
  );
}

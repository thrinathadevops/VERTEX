"use client";

import { useState } from "react";
import Link from "next/link";
import api from "@/lib/api";

export default function ForgotPassword() {
    const [email, setEmail] = useState("");
    const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
    const [message, setMessage] = useState("");

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setStatus("loading");
        setMessage("");

        try {
            const res = await api.post("/auth/forgot-password", { email });
            setStatus("success");
            setMessage(res.data?.message || "If that email exists, a reset link has been sent.");
        } catch (err: any) {
            setStatus("error");
            setMessage(err.response?.data?.detail || "Something went wrong. Please try again.");
        }
    };

    return (
        <div className="min-h-[80vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 bg-[#0a0f1c]">
            <div className="max-w-md w-full space-y-8 bg-[#111827] p-8 rounded-xl border border-slate-800 shadow-xl">
                <div>
                    <h2 className="mt-6 text-center text-3xl font-extrabold text-white">Reset Password</h2>
                    <p className="mt-4 text-center text-sm text-slate-400">
                        Enter your email address and we'll send you a link to reset your password.
                    </p>
                </div>

                {status === "success" ? (
                    <div className="rounded-md bg-emerald-500/10 p-4 border border-emerald-500/20">
                        <p className="text-sm text-emerald-400 text-center">{message}</p>
                    </div>
                ) : (
                    <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
                        {status === "error" && (
                            <div className="rounded-md bg-rose-500/10 p-4 border border-rose-500/20">
                                <p className="text-sm text-rose-400 text-center">{message}</p>
                            </div>
                        )}

                        <div>
                            <label htmlFor="email" className="sr-only">Email address</label>
                            <input
                                id="email"
                                name="email"
                                type="email"
                                required
                                className="appearance-none rounded relative block w-full px-3 py-3 border border-slate-700 bg-slate-900/50 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#0ea5e9] focus:border-transparent sm:text-sm transition-colors"
                                placeholder="Email address"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                disabled={status === "loading"}
                            />
                        </div>

                        <div>
                            <button
                                type="submit"
                                disabled={status === "loading"}
                                className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-[#0ea5e9] hover:bg-[#0284c7] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#0ea5e9] focus:ring-offset-slate-900 transition-colors disabled:opacity-70 disabled:cursor-not-allowed"
                            >
                                {status === "loading" ? "Sending..." : "Send Reset Link"}
                            </button>
                        </div>
                    </form>
                )}

                <div className="text-center mt-6">
                    <Link href="/login" className="text-sm font-medium text-[#0ea5e9] hover:text-[#38bdf8] transition-colors">
                        Back to login
                    </Link>
                </div>
            </div>
        </div>
    );
}

"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import api from "@/lib/api";

export default function ResetPassword() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const token = searchParams.get("token");

    const [password, setPassword] = useState("");
    const [confirmPassword, setConfirmPassword] = useState("");
    const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
    const [message, setMessage] = useState("");

    useEffect(() => {
        if (!token) {
            setStatus("error");
            setMessage("Invalid or missing reset token. Please request a new password reset link.");
        }
    }, [token]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!token) return;

        if (password !== confirmPassword) {
            setStatus("error");
            setMessage("Passwords do not match.");
            return;
        }

        setStatus("loading");
        setMessage("");

        try {
            const res = await api.post("/auth/reset-password", {
                token,
                new_password: password,
            });
            setStatus("success");
            setMessage(res.data?.message || "Password reset successfully. You can now log in.");

            // Redirect to login after a short delay
            setTimeout(() => {
                router.push("/login");
            }, 3000);

        } catch (err: any) {
            setStatus("error");
            setMessage(err.response?.data?.detail || "Something went wrong. Please try again or request a new reset link.");
        }
    };

    return (
        <div className="min-h-[80vh] flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8 bg-[#0a0f1c]">
            <div className="max-w-md w-full space-y-8 bg-[#111827] p-8 rounded-xl border border-slate-800 shadow-xl">
                <div>
                    <h2 className="mt-6 text-center text-3xl font-extrabold text-white">Create New Password</h2>
                    <p className="mt-4 text-center text-sm text-slate-400">
                        Please enter your new password below.
                    </p>
                </div>

                {status === "success" ? (
                    <div className="rounded-md bg-emerald-500/10 p-4 border border-emerald-500/20 text-center">
                        <p className="text-sm text-emerald-400">{message}</p>
                        <p className="text-sm text-slate-400 mt-4">Redirecting to login...</p>
                    </div>
                ) : (
                    <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
                        {status === "error" && (
                            <div className="rounded-md bg-rose-500/10 p-4 border border-rose-500/20">
                                <p className="text-sm text-rose-400 text-center">{message}</p>
                            </div>
                        )}

                        <div className="space-y-4">
                            <div>
                                <label htmlFor="password" className="sr-only">New Password</label>
                                <input
                                    id="password"
                                    name="password"
                                    type="password"
                                    required
                                    className="appearance-none rounded relative block w-full px-3 py-3 border border-slate-700 bg-slate-900/50 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#0ea5e9] focus:border-transparent sm:text-sm transition-colors"
                                    placeholder="New password (min 8 chars, 1 uppercase, 1 special)"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    disabled={status === "loading" || !token}
                                />
                            </div>

                            <div>
                                <label htmlFor="confirmPassword" className="sr-only">Confirm Password</label>
                                <input
                                    id="confirmPassword"
                                    name="confirmPassword"
                                    type="password"
                                    required
                                    className="appearance-none rounded relative block w-full px-3 py-3 border border-slate-700 bg-slate-900/50 text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-[#0ea5e9] focus:border-transparent sm:text-sm transition-colors"
                                    placeholder="Confirm new password"
                                    value={confirmPassword}
                                    onChange={(e) => setConfirmPassword(e.target.value)}
                                    disabled={status === "loading" || !token}
                                />
                            </div>
                        </div>

                        <div>
                            <button
                                type="submit"
                                disabled={status === "loading" || !token}
                                className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-lg shadow-sm text-white bg-[#0ea5e9] hover:bg-[#0284c7] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#0ea5e9] focus:ring-offset-slate-900 transition-colors disabled:opacity-70 disabled:cursor-not-allowed"
                            >
                                {status === "loading" ? "Resetting..." : "Reset Password"}
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

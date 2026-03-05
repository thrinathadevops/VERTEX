"use client";

import React, { useState } from "react";
import { UploadCloud, File as FileIcon, ArrowRightLeft, Download, CheckCircle, AlertTriangle } from "lucide-react";

interface DriftItem {
    parameter: string;
    prod_value: string;
    dr_value: string;
    status: "MATCH" | "DRIFT";
    remediation: string;
}

export default function DriftDashboard() {
    const [prodFile, setProdFile] = useState<File | null>(null);
    const [drFile, setDrFile] = useState<File | null>(null);
    const [loading, setLoading] = useState(false);
    const [driftResults, setDriftResults] = useState<DriftItem[] | null>(null);
    const [exporting, setExporting] = useState(false);

    const handleUpload = async () => {
        if (!prodFile || !drFile) {
            alert("Please upload both Prod and DR configurations.");
            return;
        }
        setLoading(true);
        setDriftResults(null);
        try {
            const formData = new FormData();
            formData.append("prod_file", prodFile);
            formData.append("dr_file", drFile);

            const res = await fetch("http://localhost:8000/api/v1/drift/analyze", {
                method: "POST",
                body: formData,
            });

            if (!res.ok) {
                throw new Error("Failed to run drift comparison");
            }

            const data = await res.json();
            setDriftResults(data.drift_results || []);
        } catch (err) {
            console.error("Comparison error:", err);
            alert("Error occurred during comparison. Is the backend running?");
        } finally {
            setLoading(false);
        }
    };

    const handleExport = async () => {
        if (!prodFile || !drFile) return;
        setExporting(true);
        try {
            const formData = new FormData();
            formData.append("prod_file", prodFile);
            formData.append("dr_file", drFile);

            const res = await fetch("http://localhost:8000/api/v1/drift/export", {
                method: "POST",
                body: formData,
            });

            if (!res.ok) {
                throw new Error("Failed to export drift report");
            }

            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "drift_report.xlsx";
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            a.remove();
        } catch (err) {
            console.error("Export error:", err);
            alert("Error occurred exporting report.");
        } finally {
            setExporting(false);
        }
    };

    // Stats
    const totalParams = driftResults?.length || 0;
    const matchCount = driftResults?.filter((r) => r.status === "MATCH").length || 0;
    const driftCount = driftResults?.filter((r) => r.status === "DRIFT").length || 0;

    return (
        <div className="w-full space-y-8 animate-in fade-in zoom-in-95 duration-500">
            {/* Upload Section */}
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-8">
                <div className="text-center mb-10">
                    <h2 className="text-2xl font-semibold text-gray-800 dark:text-gray-100">Upload Configurations</h2>
                    <p className="text-gray-500 dark:text-gray-400 mt-2">Select your Production and Disaster Recovery configuration files for analysis.</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8 relative items-center mb-10">
                    {/* Arrow connector for large screens */}
                    <div className="hidden md:flex absolute inset-0 justify-center items-center pointer-events-none">
                        <div className="bg-indigo-50 dark:bg-indigo-900/40 p-3 rounded-full border border-indigo-100 dark:border-indigo-800">
                            <ArrowRightLeft className="w-6 h-6 text-indigo-500" />
                        </div>
                    </div>

                    {/* Prod Upload */}
                    <div className="relative group p-8 border-2 border-dashed border-gray-200 dark:border-gray-600 rounded-xl hover:border-blue-400 hover:bg-blue-50/50 dark:hover:bg-blue-900/10 transition-all text-center">
                        {prodFile ? (
                            <div className="flex flex-col items-center justify-center space-y-3">
                                <div className="bg-blue-100 dark:bg-blue-900/40 p-4 rounded-full">
                                    <FileIcon className="w-8 h-8 text-blue-600 dark:text-blue-400" />
                                </div>
                                <div>
                                    <p className="font-semibold text-gray-700 dark:text-gray-200">{prodFile.name}</p>
                                    <p className="text-xs text-gray-500">{(prodFile.size / 1024).toFixed(2)} KB</p>
                                </div>
                            </div>
                        ) : (
                            <div className="flex flex-col items-center justify-center space-y-3 pb-4">
                                <div className="bg-gray-100 dark:bg-gray-700/50 p-4 rounded-full group-hover:bg-blue-100 dark:group-hover:bg-blue-900/40 transition-colors">
                                    <UploadCloud className="w-8 h-8 text-gray-400 group-hover:text-blue-500 transition-colors" />
                                </div>
                                <div>
                                    <p className="font-medium text-gray-700 dark:text-gray-200">Production Config</p>
                                    <p className="text-sm text-gray-500 mt-1">Click to select file</p>
                                </div>
                            </div>
                        )}
                        <input
                            type="file"
                            onChange={(e) => setProdFile(e.target.files?.[0] || null)}
                            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                        />
                    </div>

                    {/* DR Upload */}
                    <div className="relative group p-8 border-2 border-dashed border-gray-200 dark:border-gray-600 rounded-xl hover:border-emerald-400 hover:bg-emerald-50/50 dark:hover:bg-emerald-900/10 transition-all text-center">
                        {drFile ? (
                            <div className="flex flex-col items-center justify-center space-y-3">
                                <div className="bg-emerald-100 dark:bg-emerald-900/40 p-4 rounded-full">
                                    <FileIcon className="w-8 h-8 text-emerald-600 dark:text-emerald-400" />
                                </div>
                                <div>
                                    <p className="font-semibold text-gray-700 dark:text-gray-200">{drFile.name}</p>
                                    <p className="text-xs text-gray-500">{(drFile.size / 1024).toFixed(2)} KB</p>
                                </div>
                            </div>
                        ) : (
                            <div className="flex flex-col items-center justify-center space-y-3 pb-4">
                                <div className="bg-gray-100 dark:bg-gray-700/50 p-4 rounded-full group-hover:bg-emerald-100 dark:group-hover:bg-emerald-900/40 transition-colors">
                                    <UploadCloud className="w-8 h-8 text-gray-400 group-hover:text-emerald-500 transition-colors" />
                                </div>
                                <div>
                                    <p className="font-medium text-gray-700 dark:text-gray-200">Disaster Recovery (DR) Config</p>
                                    <p className="text-sm text-gray-500 mt-1">Click to select file</p>
                                </div>
                            </div>
                        )}
                        <input
                            type="file"
                            onChange={(e) => setDrFile(e.target.files?.[0] || null)}
                            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                        />
                    </div>
                </div>

                <div className="flex justify-center">
                    <button
                        onClick={handleUpload}
                        disabled={!prodFile || !drFile || loading}
                        className="flex items-center space-x-2 px-8 py-3.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 disabled:cursor-not-allowed text-white font-medium rounded-xl shadow-md disabled:shadow-none hover:shadow-lg transition-all"
                    >
                        {loading ? (
                            <>
                                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                                <span>Running Analysis...</span>
                            </>
                        ) : (
                            <>
                                <span>Analyze Configuration Drift</span>
                                <ArrowRightLeft className="w-4 h-4 ml-1" />
                            </>
                        )}
                    </button>
                </div>
            </div>

            {/* Results Section */}
            {driftResults && (
                <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden animate-in slide-in-from-bottom-5 duration-500">
                    <div className="p-6 border-b border-gray-100 dark:border-gray-700 flex flex-col md:flex-row justify-between items-start md:items-center space-y-4 md:space-y-0">
                        <div>
                            <h2 className="text-xl font-bold text-gray-800 dark:text-white">Analysis Summary</h2>
                            <p className="text-sm text-gray-500 mt-1">Found {driftCount} deviations out of {totalParams} parameters checked.</p>
                        </div>

                        <button
                            onClick={handleExport}
                            disabled={exporting}
                            className="flex items-center space-x-2 px-4 py-2 bg-emerald-50 hover:bg-emerald-100 dark:bg-emerald-900/30 dark:hover:bg-emerald-800/50 text-emerald-700 dark:text-emerald-400 font-medium text-sm rounded-lg transition-colors border border-emerald-200 dark:border-emerald-800"
                        >
                            <Download className="w-4 h-4" />
                            <span>{exporting ? "Exporting..." : "Export to Excel"}</span>
                        </button>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-0 border-b border-gray-100 dark:border-gray-700">
                        <div className="p-6 border-r border-gray-100 dark:border-gray-700 flex flex-col items-center justify-center">
                            <span className="text-4xl font-light text-gray-700 dark:text-gray-200">{totalParams}</span>
                            <span className="text-xs font-semibold uppercase tracking-wider text-gray-500 mt-2">Total Parameters</span>
                        </div>
                        <div className="p-6 border-r border-gray-100 dark:border-gray-700 flex flex-col items-center justify-center bg-green-50/50 dark:bg-green-900/10">
                            <span className="text-4xl font-light text-green-600 dark:text-green-400 flex items-center"><CheckCircle className="w-6 h-6 mr-2 hidden sm:block" /> {matchCount}</span>
                            <span className="text-xs font-semibold uppercase tracking-wider text-green-600 dark:text-green-500 mt-2">Matches</span>
                        </div>
                        <div className="p-6 flex flex-col items-center justify-center bg-rose-50/50 dark:bg-rose-900/10">
                            <span className="text-4xl font-light text-rose-600 dark:text-rose-400 flex items-center"><AlertTriangle className="w-6 h-6 mr-2 hidden sm:block" /> {driftCount}</span>
                            <span className="text-xs font-semibold uppercase tracking-wider text-rose-600 dark:text-rose-500 mt-2">Drifts Found</span>
                        </div>
                    </div>

                    <div className="overflow-x-auto">
                        <table className="w-full text-sm text-left">
                            <thead className="bg-gray-50 dark:bg-gray-900/50 text-gray-600 dark:text-gray-400 font-medium">
                                <tr>
                                    <th className="px-6 py-4">Parameter</th>
                                    <th className="px-6 py-4">Production Value</th>
                                    <th className="px-6 py-4">DR Value</th>
                                    <th className="px-6 py-4">Status</th>
                                    <th className="px-6 py-4">Remediation</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100 dark:divide-gray-800">
                                {driftResults.map((item, idx) => (
                                    <tr key={idx} className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors">
                                        <td className="px-6 py-4 font-mono text-xs text-gray-800 dark:text-gray-300 max-w-[200px] truncate" title={item.parameter}>{item.parameter}</td>
                                        <td className="px-6 py-4">
                                            <span className="inline-flex items-center px-2 py-1 rounded-md bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 text-xs font-mono max-w-[150px] truncate" title={String(item.prod_value)}>
                                                {String(item.prod_value)}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            <span className="inline-flex items-center px-2 py-1 rounded-md bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 text-xs font-mono max-w-[150px] truncate" title={String(item.dr_value)}>
                                                {String(item.dr_value)}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4">
                                            {item.status === "MATCH" ? (
                                                <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
                                                    Match
                                                </span>
                                            ) : (
                                                <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-rose-100 text-rose-800 dark:bg-rose-900/30 dark:text-rose-400">
                                                    Drift
                                                </span>
                                            )}
                                        </td>
                                        <td className="px-6 py-4 text-xs text-gray-500 dark:text-gray-400 max-w-[250px] truncate" title={item.remediation}>
                                            {item.remediation}
                                        </td>
                                    </tr>
                                ))}
                                {driftResults.length === 0 && (
                                    <tr>
                                        <td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                                            No parameters found in the provided configurations.
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    );
}

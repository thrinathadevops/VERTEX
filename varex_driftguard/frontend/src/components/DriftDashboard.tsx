"use client";

import React, { useState } from "react";
import { UploadCloud, File as FileIcon, ArrowRightLeft, Download, CheckCircle, AlertTriangle, Server, Key, Terminal } from "lucide-react";
import { Tab } from '@headlessui/react';
import clsx from "clsx";

interface DriftItem {
    parameter: string;
    prod_value: string;
    dr_value: string;
    status: "MATCH" | "DRIFT";
    remediation: string;
}

export default function DriftDashboard() {
    const [activeTab, setActiveTab] = useState(0);

    // Manual Upload State
    const [prodFile, setProdFile] = useState<File | null>(null);
    const [drFile, setDrFile] = useState<File | null>(null);

    // Connector State
    const [serverTarget, setServerTarget] = useState("192.168.1.100");
    const [serverUser, setServerUser] = useState("root");
    const [serverPassword, setServerPassword] = useState("");
    const [configPath, setConfigPath] = useState("/etc/nginx/nginx.conf");
    const [connectorType, setConnectorType] = useState("ssh");

    // Global UI State
    const [loading, setLoading] = useState(false);
    const [driftResults, setDriftResults] = useState<DriftItem[] | null>(null);
    const [exporting, setExporting] = useState(false);

    const handleManualUpload = async () => {
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

            if (!res.ok) throw new Error("Failed to run drift comparison");

            const data = await res.json();
            setDriftResults(data.drift_results || []);
        } catch (err) {
            console.error(err);
            alert("Error occurred during comparison.");
        } finally {
            setLoading(false);
        }
    };

    const handleConnectorFetch = async () => {
        if (!serverTarget || !serverUser || !configPath) {
            alert("Please fill all required connector fields.");
            return;
        }
        setLoading(true);
        try {
            // In a real flow, you'll fetch prod server config, then fetch dr server config
            // and THEN run analyze_drift on those two payloads.
            // For this MVP UI, we'll demonstrate just fetching ONE payload first to prove it works.
            const payload = {
                connector_type: connectorType,
                target: serverTarget,
                config_path: configPath,
                credentials: {
                    username: serverUser,
                    password: serverPassword
                }
            };

            const res = await fetch("http://localhost:8000/api/v1/connectors/fetch", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });

            if (!res.ok) throw new Error("Failed connecting to server");
            const data = await res.json();

            alert(`Successfully fetched config from ${serverTarget}!\n\nPreview:\n${data.content.substring(0, 100)}...`);
            // Further logic: Set prodFile = createBlob(data.content), repeat for DR.
        } catch (err) {
            console.error(err);
            alert("Error fetching from server. Ensure the backend and dummy server are running.");
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

            if (!res.ok) throw new Error("Failed to export");

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
            console.error(err);
        } finally {
            setExporting(false);
        }
    };

    const totalParams = driftResults?.length || 0;
    const matchCount = driftResults?.filter((r) => r.status === "MATCH").length || 0;
    const driftCount = driftResults?.filter((r) => r.status === "DRIFT").length || 0;

    return (
        <div className="w-full space-y-8 animate-in fade-in zoom-in-95 duration-500">

            {/* Input Mode Tabs */}
            <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-8">
                <Tab.Group selectedIndex={activeTab} onChange={setActiveTab}>
                    <Tab.List className="flex space-x-2 rounded-xl bg-gray-100 dark:bg-gray-900/50 p-1 mb-8">
                        <Tab className={({ selected }) =>
                            clsx(
                                "w-full rounded-lg py-3 text-sm font-medium leading-5 transition-all text-center flex items-center justify-center focus:outline-none",
                                selected
                                    ? "bg-white dark:bg-gray-800 text-indigo-700 dark:text-indigo-400 shadow"
                                    : "text-gray-500 hover:bg-white/[0.12] hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                            )
                        }>
                            <UploadCloud className="w-4 h-4 mr-2" /> Manual Upload
                        </Tab>
                        <Tab className={({ selected }) =>
                            clsx(
                                "w-full rounded-lg py-3 text-sm font-medium leading-5 transition-all text-center flex items-center justify-center focus:outline-none",
                                selected
                                    ? "bg-white dark:bg-gray-800 text-indigo-700 dark:text-indigo-400 shadow"
                                    : "text-gray-500 hover:bg-white/[0.12] hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                            )
                        }>
                            <Server className="w-4 h-4 mr-2" /> Automated Server Connectors (New)
                        </Tab>
                    </Tab.List>

                    <Tab.Panels>
                        {/* PANEL 1: MANUAL */}
                        <Tab.Panel>
                            <div className="text-center mb-10">
                                <h2 className="text-2xl font-semibold text-gray-800 dark:text-gray-100">Upload Configurations</h2>
                                <p className="text-gray-500 dark:text-gray-400 mt-2">Select your Production and Disaster Recovery configuration files for analysis.</p>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 relative items-center mb-10">
                                <div className="relative group p-8 border-2 border-dashed border-gray-200 dark:border-gray-600 rounded-xl hover:border-blue-400 hover:bg-blue-50/50 transition-all text-center">
                                    {prodFile ? (
                                        <div><p className="font-semibold">{prodFile.name}</p></div>
                                    ) : (
                                        <div className="flex flex-col items-center justify-center space-y-3 pb-4">
                                            <UploadCloud className="w-8 h-8 text-gray-400 group-hover:text-blue-500 transition-colors" />
                                            <p className="font-medium">Production Config</p>
                                        </div>
                                    )}
                                    <input type="file" onChange={(e) => setProdFile(e.target.files?.[0] || null)} className="absolute inset-0 w-full h-full opacity-0 cursor-pointer" />
                                </div>

                                <div className="relative group p-8 border-2 border-dashed border-gray-200 dark:border-gray-600 rounded-xl hover:border-emerald-400 hover:bg-emerald-50/50 transition-all text-center">
                                    {drFile ? (
                                        <div><p className="font-semibold">{drFile.name}</p></div>
                                    ) : (
                                        <div className="flex flex-col items-center justify-center space-y-3 pb-4">
                                            <UploadCloud className="w-8 h-8 text-gray-400 group-hover:text-emerald-500 transition-colors" />
                                            <p className="font-medium">DR Config</p>
                                        </div>
                                    )}
                                    <input type="file" onChange={(e) => setDrFile(e.target.files?.[0] || null)} className="absolute inset-0 w-full h-full opacity-0 cursor-pointer" />
                                </div>
                            </div>

                            <div className="flex justify-center">
                                <button onClick={handleManualUpload} disabled={!prodFile || !drFile || loading} className="flex items-center space-x-2 px-8 py-3.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-medium rounded-xl shadow-md transition-all">
                                    {loading ? <span>Analyzing...</span> : <span>Analyze Variables</span>}
                                </button>
                            </div>
                        </Tab.Panel>

                        {/* PANEL 2: CONNECTORS */}
                        <Tab.Panel>
                            <div className="mb-10 text-center">
                                <h2 className="text-2xl font-semibold text-gray-800 dark:text-gray-100">Live Server Extraction</h2>
                                <p className="text-gray-500 dark:text-gray-400 mt-2">Connect to your servers or cloud accounts directly.</p>
                            </div>

                            <div className="flex flex-wrap gap-2 mb-6 justify-center">
                                <button onClick={() => setConnectorType("ssh")} className={clsx("px-4 py-2 rounded-full text-sm font-medium transition-colors cursor-pointer", connectorType === "ssh" ? "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/50 dark:text-indigo-300" : "bg-gray-50 text-gray-500 hover:bg-gray-100")}><Terminal className="w-4 h-4 inline mr-1.5" /> SSH</button>
                                <button onClick={() => setConnectorType("winrm")} className={clsx("px-4 py-2 rounded-full text-sm font-medium transition-colors cursor-pointer", connectorType === "winrm" ? "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/50 dark:text-indigo-300" : "bg-gray-50 text-gray-500 hover:bg-gray-100")}><Server className="w-4 h-4 inline mr-1.5" /> WinRM</button>
                                <button onClick={() => setConnectorType("aws")} className={clsx("px-4 py-2 rounded-full text-sm font-medium transition-colors cursor-pointer", connectorType === "aws" ? "bg-orange-100 text-orange-700 dark:bg-orange-900/50 dark:text-orange-300" : "bg-gray-50 text-gray-500 hover:bg-gray-100")}><UploadCloud className="w-4 h-4 inline mr-1.5" /> AWS</button>
                                <button onClick={() => setConnectorType("azure")} className={clsx("px-4 py-2 rounded-full text-sm font-medium transition-colors cursor-pointer", connectorType === "azure" ? "bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300" : "bg-gray-50 text-gray-500 hover:bg-gray-100")}><UploadCloud className="w-4 h-4 inline mr-1.5" /> Azure</button>
                                <button onClick={() => setConnectorType("gcp")} className={clsx("px-4 py-2 rounded-full text-sm font-medium transition-colors cursor-pointer", connectorType === "gcp" ? "bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300" : "bg-gray-50 text-gray-500 hover:bg-gray-100")}><UploadCloud className="w-4 h-4 inline mr-1.5" /> GCP</button>
                                <button onClick={() => setConnectorType("gitops")} className={clsx("px-4 py-2 rounded-full text-sm font-medium transition-colors cursor-pointer", connectorType === "gitops" ? "bg-purple-100 text-purple-700 dark:bg-purple-900/50 dark:text-purple-300" : "bg-gray-50 text-gray-500 hover:bg-gray-100")}><FileIcon className="w-4 h-4 inline mr-1.5" /> GitOps (GitHub/GitLab)</button>
                            </div>

                            <div className="space-y-4 max-w-2xl mx-auto mb-8">
                                {(connectorType === "ssh" || connectorType === "winrm") && (
                                    <>
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Target Host (IP or Domain)</label>
                                            <input type="text" value={serverTarget} onChange={e => setServerTarget(e.target.value)} className="w-full px-4 py-2 border rounded-lg focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-900 border-gray-300 dark:border-gray-700" placeholder="e.g. 192.168.1.10" />
                                        </div>
                                        <div className="flex gap-4">
                                            <div className="flex-1">
                                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Username</label>
                                                <input type="text" value={serverUser} onChange={e => setServerUser(e.target.value)} className="w-full px-4 py-2 border rounded-lg focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-900 border-gray-300 dark:border-gray-700" placeholder="root or administrator" />
                                            </div>
                                            <div className="flex-1">
                                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Password</label>
                                                <input type="password" value={serverPassword} onChange={e => setServerPassword(e.target.value)} className="w-full px-4 py-2 border rounded-lg focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-900 border-gray-300 dark:border-gray-700" placeholder="••••••••" />
                                            </div>
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Configuration Path</label>
                                            <input type="text" value={configPath} onChange={e => setConfigPath(e.target.value)} className="w-full px-4 py-2 border rounded-lg focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-900 border-gray-300 dark:border-gray-700" placeholder="/etc/nginx/nginx.conf or C:\inetpub\temp\appCmd.config" />
                                        </div>
                                    </>
                                )}

                                {connectorType === "aws" && (
                                    <>
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Target (Service | Region)</label>
                                            <input type="text" value={serverTarget} onChange={e => setServerTarget(e.target.value)} className="w-full px-4 py-2 border rounded-lg" placeholder="ec2|us-east-1" />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">AWS Access Key ID</label>
                                            <input type="text" value={serverUser} onChange={e => setServerUser(e.target.value)} className="w-full px-4 py-2 border rounded-lg" placeholder="AKIA..." />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">AWS Secret Access Key</label>
                                            <input type="password" value={serverPassword} onChange={e => setServerPassword(e.target.value)} className="w-full px-4 py-2 border rounded-lg" placeholder="••••••••" />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Resource Path (Type | ID)</label>
                                            <input type="text" value={configPath} onChange={e => setConfigPath(e.target.value)} className="w-full px-4 py-2 border rounded-lg" placeholder="instance|i-1234567" />
                                        </div>
                                    </>
                                )}

                                {connectorType === "azure" && (
                                    <div className="bg-yellow-50 p-4 rounded-xl text-yellow-800 text-sm border border-yellow-200">
                                        Azure integration currently expects Tenant ID/Client ID mapped to the local UI variables in the background, targeting an ARM resource directly.
                                        <input type="text" placeholder="subscription_id|resource_group" className="w-full px-4 py-2 mt-2 border rounded-lg" value={serverTarget} onChange={e => setServerTarget(e.target.value)} />
                                        <input type="text" placeholder="Microsoft.Compute/virtualMachines|vm_name" className="w-full px-4 py-2 mt-2 border rounded-lg" value={configPath} onChange={e => setConfigPath(e.target.value)} />
                                    </div>
                                )}

                                {connectorType === "gcp" && (
                                    <div className="bg-green-50 p-4 rounded-xl text-green-800 text-sm border border-green-200">
                                        GCP integration currently uses `target = project_id|zone` and `path = compute|instances|name`.
                                        <input type="text" placeholder="project-id-123|us-central1-a" className="w-full px-4 py-2 mt-2 border rounded-lg" value={serverTarget} onChange={e => setServerTarget(e.target.value)} />
                                        <input type="text" placeholder="compute|instances|my-instance" className="w-full px-4 py-2 mt-2 border rounded-lg" value={configPath} onChange={e => setConfigPath(e.target.value)} />
                                    </div>
                                )}

                                {connectorType === "gitops" && (
                                    <>
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Git Repository URL</label>
                                            <input type="text" value={serverTarget} onChange={e => setServerTarget(e.target.value)} className="w-full px-4 py-2 border rounded-lg focus:ring-purple-500 focus:border-purple-500 dark:bg-gray-900 border-gray-300 dark:border-gray-700" placeholder="https://github.com/org/repo.git" />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Personal Access Token (if private)</label>
                                            <input type="password" value={serverPassword} onChange={e => setServerPassword(e.target.value)} className="w-full px-4 py-2 border rounded-lg focus:ring-purple-500 focus:border-purple-500 dark:bg-gray-900 border-gray-300 dark:border-gray-700" placeholder="ghp_xxxxxxxxxxxx" />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">File Path in Repository</label>
                                            <input type="text" value={configPath} onChange={e => setConfigPath(e.target.value)} className="w-full px-4 py-2 border rounded-lg focus:ring-purple-500 focus:border-purple-500 dark:bg-gray-900 border-gray-300 dark:border-gray-700" placeholder="k8s/deployment.yaml" />
                                        </div>
                                    </>
                                )}
                            </div>

                            <div className="bg-indigo-50 dark:bg-indigo-900/20 p-4 rounded-xl text-sm text-indigo-800 dark:text-indigo-300 max-w-2xl mx-auto flex items-start mb-8 border border-indigo-100 dark:border-indigo-800/50">
                                <Key className="w-5 h-5 mr-3 flex-shrink-0 mt-0.5" />
                                <p>In production, API keys and credentials should be managed via Secrets Manager or HashiCorp vault. For this demo, values are passed securely to the robust Python SDK backend over the local proxy.</p>
                            </div>

                            <div className="flex justify-center">
                                <button onClick={handleConnectorFetch} disabled={loading} className="flex items-center space-x-2 px-8 py-3.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-medium rounded-xl shadow-md transition-all">
                                    {loading ? <span>Connecting to Source...</span> : <span>Fetch Configuration Remotely</span>}
                                </button>
                            </div>
                        </Tab.Panel>
                    </Tab.Panels>
                </Tab.Group>
            </div>

            {/* Results Section */}
            {driftResults && (
                <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden mt-8 animate-in slide-in-from-bottom-5 duration-500">
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

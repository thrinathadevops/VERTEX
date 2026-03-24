"use client";

import React, { useState, useEffect } from "react";
import {
    UploadCloud,
    File as FileIcon,
    Download,
    CheckCircle,
    AlertTriangle,
    Server,
    Key,
    Terminal,
} from "lucide-react";
import { Tab } from "@headlessui/react";
import clsx from "clsx";
import {
    motion,
    AnimatePresence,
    useMotionValue,
    useSpring,
    useTransform,
    type Variants,
} from "framer-motion";

// ─── Types ───────────────────────────────────────────────────────────────────
interface DriftItem {
    parameter: string;
    prod_value: string;
    dr_value: string;
    status: "MATCH" | "DRIFT";
    remediation: string;
}

// ─── Animation Variants ───────────────────────────────────────────────────────
const SPRING_FAST = { type: "spring" as const, stiffness: 350, damping: 22 };
const SPRING_MED  = { type: "spring" as const, stiffness: 200, damping: 24 };
const SPRING_SLOW = { type: "spring" as const, stiffness: 140, damping: 20 };

const fadeUp: Variants = {
    hidden: { opacity: 0, y: 24 },
    visible: (i: number = 0) => ({
        opacity: 1, y: 0,
        transition: { delay: i * 0.06, ...SPRING_MED },
    }),
    exit: { opacity: 0, y: -16, transition: { duration: 0.2 } },
};

const staggerContainer: Variants = {
    hidden: {},
    visible: { transition: { staggerChildren: 0.07 } },
};

const rowVariant: Variants = {
    hidden: { opacity: 0, x: -12 },
    visible: (i: number) => ({
        opacity: 1, x: 0,
        transition: { delay: i * 0.04, ...SPRING_MED },
    }),
};

const statCardVariant: Variants = {
    hidden: { opacity: 0, y: 20, scale: 0.96 },
    visible: (i: number) => ({
        opacity: 1, y: 0, scale: 1,
        transition: { delay: i * 0.1, ...SPRING_SLOW },
    }),
};

const tabPanelVariant: Variants = {
    hidden:  { opacity: 0, x: 30 },
    visible: { opacity: 1, x: 0, transition: SPRING_MED },
    exit:    { opacity: 0, x: -30, transition: { duration: 0.15 } },
};

// ─── Animated Counter ─────────────────────────────────────────────────────────
function AnimatedNumber({ value }: { value: number }) {
    const mv = useMotionValue(0);
    const spring = useSpring(mv, { stiffness: 80, damping: 18 });
    const display = useTransform(spring, (v) => Math.round(v).toString());

    useEffect(() => { mv.set(value); }, [value, mv]);

    return <motion.span>{display}</motion.span>;
}

// ─── Drop Zone ────────────────────────────────────────────────────────────────
interface DropZoneProps {
    label: string;
    file: File | null;
    onChange: (file: File | null) => void;
    accent: "blue" | "emerald";
}

function DropZone({ label, file, onChange, accent }: DropZoneProps) {
    const borderHover = accent === "blue"
        ? "hover:border-blue-400 hover:bg-blue-50/50 dark:hover:bg-blue-900/10"
        : "hover:border-emerald-400 hover:bg-emerald-50/50 dark:hover:bg-emerald-900/10";
    const iconClass   = accent === "blue" ? "group-hover:text-blue-500" : "group-hover:text-emerald-500";
    const glowColor   = accent === "blue" ? "rgba(96,165,250,0.3)" : "rgba(52,211,153,0.3)";

    return (
        <motion.div
            whileHover={{ scale: 1.025, boxShadow: `0 0 0 3px ${glowColor}` }}
            whileTap={{ scale: 0.98 }}
            transition={SPRING_FAST}
            className={clsx(
                "relative group p-8 border-2 border-dashed border-gray-200 dark:border-gray-600 rounded-xl transition-all text-center cursor-pointer",
                borderHover
            )}
        >
            {file ? (
                <motion.div
                    key={file.name}
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ type: "spring" as const, stiffness: 260, damping: 20 }}
                >
                    <p className="font-semibold text-gray-800 dark:text-gray-100">{file.name}</p>
                    <p className="text-xs text-gray-400 mt-1">{(file.size / 1024).toFixed(1)} KB</p>
                </motion.div>
            ) : (
                <div className="flex flex-col items-center justify-center space-y-3 pb-4">
                    <motion.div
                        animate={{ y: [0, -5, 0] }}
                        transition={{ duration: 2.4, repeat: Infinity, ease: "easeInOut" }}
                    >
                        <UploadCloud className={clsx("w-8 h-8 text-gray-400 transition-colors", iconClass)} />
                    </motion.div>
                    <p className="font-medium text-gray-600 dark:text-gray-400">{label}</p>
                </div>
            )}
            <input
                type="file"
                onChange={(e) => onChange(e.target.files?.[0] || null)}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
        </motion.div>
    );
}

// ─── Spinner ─────────────────────────────────────────────────────────────────
function Spinner() {
    return (
        <motion.span
            animate={{ rotate: 360 }}
            transition={{ duration: 0.9, repeat: Infinity, ease: "linear" }}
            className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full"
        />
    );
}

// ─── Main Dashboard ───────────────────────────────────────────────────────────
export default function DriftDashboard() {
    const [activeTab, setActiveTab]         = useState(0);
    const [prodFile, setProdFile]           = useState<File | null>(null);
    const [drFile, setDrFile]               = useState<File | null>(null);
    const [serverTarget, setServerTarget]   = useState("192.168.1.100");
    const [serverUser, setServerUser]       = useState("root");
    const [serverPassword, setServerPassword] = useState("");
    const [configPath, setConfigPath]       = useState("/etc/nginx/nginx.conf");
    const [connectorType, setConnectorType] = useState("ssh");
    const [loading, setLoading]             = useState(false);
    const [driftResults, setDriftResults]   = useState<DriftItem[] | null>(null);
    const [exporting, setExporting]         = useState(false);

    const handleManualUpload = async () => {
        if (!prodFile || !drFile) { alert("Please upload both Prod and DR configurations."); return; }
        setLoading(true); setDriftResults(null);
        try {
            const formData = new FormData();
            formData.append("prod_file", prodFile);
            formData.append("dr_file", drFile);
            const res = await fetch("http://localhost:8000/api/v1/drift/analyze", { method: "POST", body: formData });
            if (!res.ok) throw new Error("Failed to run drift comparison");
            const data = await res.json();
            setDriftResults(data.drift_results || []);
        } catch (err) {
            console.error(err);
            alert("Error occurred during comparison.");
        } finally { setLoading(false); }
    };

    const handleConnectorFetch = async () => {
        if (!serverTarget || !serverUser || !configPath) { alert("Please fill all required connector fields."); return; }
        setLoading(true);
        try {
            const payload = { connector_type: connectorType, target: serverTarget, config_path: configPath, credentials: { username: serverUser, password: serverPassword } };
            const res = await fetch("http://localhost:8000/api/v1/connectors/fetch", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
            if (!res.ok) throw new Error("Failed connecting to server");
            const data = await res.json();
            alert(`Successfully fetched config from ${serverTarget}!\n\nPreview:\n${data.content.substring(0, 100)}...`);
        } catch (err) {
            console.error(err);
            alert("Error fetching from server. Ensure the backend and dummy server are running.");
        } finally { setLoading(false); }
    };

    const handleExport = async () => {
        if (!prodFile || !drFile) return;
        setExporting(true);
        try {
            const formData = new FormData();
            formData.append("prod_file", prodFile);
            formData.append("dr_file", drFile);
            const res = await fetch("http://localhost:8000/api/v1/drift/export", { method: "POST", body: formData });
            if (!res.ok) throw new Error("Failed to export");
            const blob  = await res.blob();
            const url   = window.URL.createObjectURL(blob);
            const a     = document.createElement("a");
            a.href = url; a.download = "drift_report.xlsx";
            document.body.appendChild(a); a.click();
            window.URL.revokeObjectURL(url); a.remove();
        } catch (err) { console.error(err); }
        finally { setExporting(false); }
    };

    const totalParams = driftResults?.length || 0;
    const matchCount  = driftResults?.filter((r) => r.status === "MATCH").length || 0;
    const driftCount  = driftResults?.filter((r) => r.status === "DRIFT").length || 0;

    const connectorPills = [
        { id: "ssh",    label: "SSH",                   icon: <Terminal   className="w-4 h-4 inline mr-1.5" />, colorActive: "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/50 dark:text-indigo-300" },
        { id: "winrm",  label: "WinRM",                 icon: <Server     className="w-4 h-4 inline mr-1.5" />, colorActive: "bg-indigo-100 text-indigo-700 dark:bg-indigo-900/50 dark:text-indigo-300" },
        { id: "aws",    label: "AWS",                   icon: <UploadCloud className="w-4 h-4 inline mr-1.5" />, colorActive: "bg-orange-100 text-orange-700 dark:bg-orange-900/50 dark:text-orange-300" },
        { id: "azure",  label: "Azure",                 icon: <UploadCloud className="w-4 h-4 inline mr-1.5" />, colorActive: "bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300" },
        { id: "gcp",    label: "GCP",                   icon: <UploadCloud className="w-4 h-4 inline mr-1.5" />, colorActive: "bg-green-100 text-green-700 dark:bg-green-900/50 dark:text-green-300" },
        { id: "gitops", label: "GitOps (GitHub/GitLab)", icon: <FileIcon   className="w-4 h-4 inline mr-1.5" />, colorActive: "bg-purple-100 text-purple-700 dark:bg-purple-900/50 dark:text-purple-300" },
    ];

    const inputCls = "w-full px-4 py-2 border rounded-lg focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-900 border-gray-300 dark:border-gray-700 dark:text-gray-100";

    return (
        <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="w-full space-y-8">

            {/* ── Input Card ── */}
            <motion.div
                variants={fadeUp}
                custom={0}
                className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 p-8"
            >
                <Tab.Group selectedIndex={activeTab} onChange={setActiveTab}>
                    <Tab.List className="flex space-x-2 rounded-xl bg-gray-100 dark:bg-gray-900/50 p-1 mb-8">
                        {["Manual Upload", "Automated Server Connectors (New)"].map((label, idx) => (
                            <Tab key={label} className={({ selected }) =>
                                clsx(
                                    "w-full rounded-lg py-3 text-sm font-medium leading-5 transition-all text-center flex items-center justify-center focus:outline-none",
                                    selected
                                        ? "bg-white dark:bg-gray-800 text-indigo-700 dark:text-indigo-400 shadow"
                                        : "text-gray-500 hover:bg-white/[0.12] hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
                                )
                            }>
                                {idx === 0 ? <UploadCloud className="w-4 h-4 mr-2" /> : <Server className="w-4 h-4 mr-2" />}
                                {label}
                            </Tab>
                        ))}
                    </Tab.List>

                    <Tab.Panels>
                        <AnimatePresence mode="wait" initial={false}>
                            {/* ── Panel 1: Manual Upload ── */}
                            {activeTab === 0 && (
                                <Tab.Panel static key="manual">
                                    <motion.div key="manual-anim" variants={tabPanelVariant} initial="hidden" animate="visible" exit="exit">
                                        <div className="text-center mb-10">
                                            <h2 className="text-2xl font-semibold text-gray-800 dark:text-gray-100">Upload Configurations</h2>
                                            <p className="text-gray-500 dark:text-gray-400 mt-2">Select your Production and Disaster Recovery configuration files for analysis.</p>
                                        </div>

                                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-10">
                                            <DropZone label="Production Config" file={prodFile} onChange={setProdFile} accent="blue"    />
                                            <DropZone label="DR Config"         file={drFile}   onChange={setDrFile}   accent="emerald" />
                                        </div>

                                        <div className="flex justify-center">
                                            <motion.button
                                                onClick={handleManualUpload}
                                                disabled={!prodFile || !drFile || loading}
                                                whileHover={{ scale: 1.04 }}
                                                whileTap={{ scale: 0.95 }}
                                                transition={SPRING_FAST}
                                                className="flex items-center gap-2 px-8 py-3.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-medium rounded-xl shadow-md transition-colors"
                                            >
                                                <AnimatePresence mode="wait">
                                                    {loading
                                                        ? <motion.span key="ld" className="flex items-center gap-2" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}><Spinner />Analyzing...</motion.span>
                                                        : <motion.span key="id" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>Analyze Variables</motion.span>
                                                    }
                                                </AnimatePresence>
                                            </motion.button>
                                        </div>
                                    </motion.div>
                                </Tab.Panel>
                            )}

                            {/* ── Panel 2: Connectors ── */}
                            {activeTab === 1 && (
                                <Tab.Panel static key="connectors">
                                    <motion.div key="conn-anim" variants={tabPanelVariant} initial="hidden" animate="visible" exit="exit">
                                        <div className="mb-10 text-center">
                                            <h2 className="text-2xl font-semibold text-gray-800 dark:text-gray-100">Live Server Extraction</h2>
                                            <p className="text-gray-500 dark:text-gray-400 mt-2">Connect to your servers or cloud accounts directly.</p>
                                        </div>

                                        <div className="flex flex-wrap gap-2 mb-6 justify-center">
                                            {connectorPills.map((pill) => (
                                                <motion.button
                                                    key={pill.id}
                                                    onClick={() => setConnectorType(pill.id)}
                                                    whileHover={{ scale: 1.07 }}
                                                    whileTap={{ scale: 0.93 }}
                                                    transition={SPRING_FAST}
                                                    className={clsx(
                                                        "px-4 py-2 rounded-full text-sm font-medium cursor-pointer transition-colors",
                                                        connectorType === pill.id ? pill.colorActive : "bg-gray-50 dark:bg-gray-700 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-600"
                                                    )}
                                                >
                                                    {pill.icon}{pill.label}
                                                </motion.button>
                                            ))}
                                        </div>

                                        {/* Connector-specific fields */}
                                        <AnimatePresence mode="wait">
                                            <motion.div
                                                key={connectorType}
                                                initial={{ opacity: 0, y: 12 }}
                                                animate={{ opacity: 1, y: 0 }}
                                                exit={{ opacity: 0, y: -8 }}
                                                transition={SPRING_MED}
                                                className="space-y-4 max-w-2xl mx-auto mb-8"
                                            >
                                                {(connectorType === "ssh" || connectorType === "winrm") && (
                                                    <>
                                                        <div>
                                                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Target Host (IP or Domain)</label>
                                                            <input type="text" value={serverTarget} onChange={e => setServerTarget(e.target.value)} className={inputCls} placeholder="e.g. 192.168.1.10" />
                                                        </div>
                                                        <div className="flex gap-4">
                                                            <div className="flex-1">
                                                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Username</label>
                                                                <input type="text" value={serverUser} onChange={e => setServerUser(e.target.value)} className={inputCls} placeholder="root or administrator" />
                                                            </div>
                                                            <div className="flex-1">
                                                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Password</label>
                                                                <input type="password" value={serverPassword} onChange={e => setServerPassword(e.target.value)} className={inputCls} placeholder="••••••••" />
                                                            </div>
                                                        </div>
                                                        <div>
                                                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Configuration Path</label>
                                                            <input type="text" value={configPath} onChange={e => setConfigPath(e.target.value)} className={inputCls} placeholder="/etc/nginx/nginx.conf" />
                                                        </div>
                                                    </>
                                                )}
                                                {connectorType === "aws" && (
                                                    <>
                                                        <div>
                                                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Target (Service | Region)</label>
                                                            <input type="text" value={serverTarget} onChange={e => setServerTarget(e.target.value)} className={inputCls} placeholder="ec2|us-east-1" />
                                                        </div>
                                                        <div>
                                                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">AWS Access Key ID</label>
                                                            <input type="text" value={serverUser} onChange={e => setServerUser(e.target.value)} className={inputCls} placeholder="AKIA..." />
                                                        </div>
                                                        <div>
                                                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">AWS Secret Access Key</label>
                                                            <input type="password" value={serverPassword} onChange={e => setServerPassword(e.target.value)} className={inputCls} placeholder="••••••••" />
                                                        </div>
                                                        <div>
                                                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Resource Path (Type | ID)</label>
                                                            <input type="text" value={configPath} onChange={e => setConfigPath(e.target.value)} className={inputCls} placeholder="instance|i-1234567" />
                                                        </div>
                                                    </>
                                                )}
                                                {connectorType === "azure" && (
                                                    <div className="bg-yellow-50 p-4 rounded-xl text-yellow-800 text-sm border border-yellow-200">
                                                        Azure integration expects Tenant ID/Client ID, targeting an ARM resource directly.
                                                        <input type="text" placeholder="subscription_id|resource_group" className="w-full px-4 py-2 mt-2 border rounded-lg" value={serverTarget} onChange={e => setServerTarget(e.target.value)} />
                                                        <input type="text" placeholder="Microsoft.Compute/virtualMachines|vm_name" className="w-full px-4 py-2 mt-2 border rounded-lg" value={configPath} onChange={e => setConfigPath(e.target.value)} />
                                                    </div>
                                                )}
                                                {connectorType === "gcp" && (
                                                    <div className="bg-green-50 p-4 rounded-xl text-green-800 text-sm border border-green-200">
                                                        GCP uses `target = project_id|zone` and `path = compute|instances|name`.
                                                        <input type="text" placeholder="project-id-123|us-central1-a" className="w-full px-4 py-2 mt-2 border rounded-lg" value={serverTarget} onChange={e => setServerTarget(e.target.value)} />
                                                        <input type="text" placeholder="compute|instances|my-instance" className="w-full px-4 py-2 mt-2 border rounded-lg" value={configPath} onChange={e => setConfigPath(e.target.value)} />
                                                    </div>
                                                )}
                                                {connectorType === "gitops" && (
                                                    <>
                                                        <div>
                                                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Git Repository URL</label>
                                                            <input type="text" value={serverTarget} onChange={e => setServerTarget(e.target.value)} className={inputCls} placeholder="https://github.com/org/repo.git" />
                                                        </div>
                                                        <div>
                                                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Personal Access Token</label>
                                                            <input type="password" value={serverPassword} onChange={e => setServerPassword(e.target.value)} className={inputCls} placeholder="ghp_xxxxxxxxxxxx" />
                                                        </div>
                                                        <div>
                                                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">File Path in Repository</label>
                                                            <input type="text" value={configPath} onChange={e => setConfigPath(e.target.value)} className={inputCls} placeholder="k8s/deployment.yaml" />
                                                        </div>
                                                    </>
                                                )}
                                            </motion.div>
                                        </AnimatePresence>

                                        <div className="bg-indigo-50 dark:bg-indigo-900/20 p-4 rounded-xl text-sm text-indigo-800 dark:text-indigo-300 max-w-2xl mx-auto flex items-start mb-8 border border-indigo-100 dark:border-indigo-800/50">
                                            <Key className="w-5 h-5 mr-3 flex-shrink-0 mt-0.5" />
                                            <p>In production, credentials should be managed via Secrets Manager or HashiCorp Vault. For this demo, values are passed securely to the backend.</p>
                                        </div>

                                        <div className="flex justify-center">
                                            <motion.button
                                                onClick={handleConnectorFetch}
                                                disabled={loading}
                                                whileHover={{ scale: 1.04 }}
                                                whileTap={{ scale: 0.95 }}
                                                transition={SPRING_FAST}
                                                className="flex items-center gap-2 px-8 py-3.5 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-medium rounded-xl shadow-md transition-colors"
                                            >
                                                <AnimatePresence mode="wait">
                                                    {loading
                                                        ? <motion.span key="cl" className="flex items-center gap-2" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}><Spinner />Connecting to Source...</motion.span>
                                                        : <motion.span key="ci" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>Fetch Configuration Remotely</motion.span>
                                                    }
                                                </AnimatePresence>
                                            </motion.button>
                                        </div>
                                    </motion.div>
                                </Tab.Panel>
                            )}
                        </AnimatePresence>
                    </Tab.Panels>
                </Tab.Group>
            </motion.div>

            {/* ── Results Section ── */}
            <AnimatePresence>
                {driftResults && (
                    <motion.div
                        key="results"
                        initial={{ opacity: 0, y: 40 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: 20 }}
                        transition={SPRING_SLOW}
                        className="bg-white dark:bg-gray-800 rounded-2xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden"
                    >
                        {/* Header */}
                        <div className="p-6 border-b border-gray-100 dark:border-gray-700 flex flex-col md:flex-row justify-between items-start md:items-center space-y-4 md:space-y-0">
                            <div>
                                <h2 className="text-xl font-bold text-gray-800 dark:text-white">Analysis Summary</h2>
                                <p className="text-sm text-gray-500 mt-1">Found {driftCount} deviations out of {totalParams} parameters checked.</p>
                            </div>
                            <motion.button
                                onClick={handleExport}
                                disabled={exporting}
                                whileHover={{ scale: 1.04 }}
                                whileTap={{ scale: 0.96 }}
                                transition={SPRING_FAST}
                                className="flex items-center gap-2 px-4 py-2 bg-emerald-50 hover:bg-emerald-100 dark:bg-emerald-900/30 dark:hover:bg-emerald-800/50 text-emerald-700 dark:text-emerald-400 font-medium text-sm rounded-lg transition-colors border border-emerald-200 dark:border-emerald-800"
                            >
                                <Download className="w-4 h-4" />
                                <span>{exporting ? "Exporting..." : "Export to Excel"}</span>
                            </motion.button>
                        </div>

                        {/* Stat Cards */}
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-0 border-b border-gray-100 dark:border-gray-700">
                            {[
                                { value: totalParams, label: "Total Parameters", cls: "border-r border-gray-100 dark:border-gray-700",                          valCls: "text-gray-700 dark:text-gray-200",         icon: null },
                                { value: matchCount,  label: "Matches",          cls: "border-r border-gray-100 dark:border-gray-700 bg-green-50/50 dark:bg-green-900/10", valCls: "text-green-600 dark:text-green-400",  icon: <CheckCircle   className="w-6 h-6 mr-2 hidden sm:block" /> },
                                { value: driftCount,  label: "Drifts Found",     cls: "bg-rose-50/50 dark:bg-rose-900/10",                                       valCls: "text-rose-600 dark:text-rose-400",         icon: <AlertTriangle className="w-6 h-6 mr-2 hidden sm:block" /> },
                            ].map((stat, i) => (
                                <motion.div
                                    key={stat.label}
                                    variants={statCardVariant}
                                    custom={i}
                                    initial="hidden"
                                    animate="visible"
                                    className={clsx("p-6 flex flex-col items-center justify-center", stat.cls)}
                                >
                                    <span className={clsx("text-4xl font-light flex items-center", stat.valCls)}>
                                        {stat.icon}<AnimatedNumber value={stat.value} />
                                    </span>
                                    <span className="text-xs font-semibold uppercase tracking-wider text-gray-500 mt-2">{stat.label}</span>
                                </motion.div>
                            ))}
                        </div>

                        {/* Table */}
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
                                <motion.tbody
                                    variants={staggerContainer}
                                    initial="hidden"
                                    animate="visible"
                                    className="divide-y divide-gray-100 dark:divide-gray-800"
                                >
                                    {driftResults.map((item, idx) => (
                                        <motion.tr
                                            key={idx}
                                            variants={rowVariant}
                                            custom={idx}
                                            className="hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
                                        >
                                            <td className="px-6 py-4 font-mono text-xs text-gray-800 dark:text-gray-300 max-w-[200px] truncate" title={item.parameter}>{item.parameter}</td>
                                            <td className="px-6 py-4">
                                                <span className="inline-flex items-center px-2 py-1 rounded-md bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 text-xs font-mono max-w-[150px] truncate" title={String(item.prod_value)}>{String(item.prod_value)}</span>
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className="inline-flex items-center px-2 py-1 rounded-md bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 text-xs font-mono max-w-[150px] truncate" title={String(item.dr_value)}>{String(item.dr_value)}</span>
                                            </td>
                                            <td className="px-6 py-4">
                                                <motion.span
                                                    initial={{ scale: 0, opacity: 0 }}
                                                    animate={{ scale: 1, opacity: 1 }}
                                                    transition={{ type: "spring" as const, stiffness: 300, damping: 18, delay: idx * 0.04 + 0.1 }}
                                                    className={clsx(
                                                        "inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium",
                                                        item.status === "MATCH"
                                                            ? "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400"
                                                            : "bg-rose-100 text-rose-800 dark:bg-rose-900/30 dark:text-rose-400"
                                                    )}
                                                >
                                                    {item.status === "MATCH" ? "Match" : "Drift"}
                                                </motion.span>
                                            </td>
                                            <td className="px-6 py-4 text-xs text-gray-500 dark:text-gray-400 max-w-[250px] truncate" title={item.remediation}>{item.remediation}</td>
                                        </motion.tr>
                                    ))}
                                    {driftResults.length === 0 && (
                                        <tr>
                                            <td colSpan={5} className="px-6 py-12 text-center text-gray-500">No parameters found in the provided configurations.</td>
                                        </tr>
                                    )}
                                </motion.tbody>
                            </table>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
}

import DriftDashboard from "@/components/DriftDashboard";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "VAREX DriftGuard — Configuration Drift Analysis",
  description: "Detect and remediate configuration drift between Production and DR environments.",
};

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        <AnimatedHeader />
        <DriftDashboard />
      </div>
    </main>
  );
}

// Server component can't use framer-motion, so isolate animated header
import AnimatedHeader from "@/components/AnimatedHeader";

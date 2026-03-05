import DriftDashboard from "@/components/DriftDashboard";

export default function Home() {
  return (
    <main className="min-h-screen bg-gray-50 dark:bg-gray-900 p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center space-x-3 mb-8">
          <div className="bg-indigo-600 p-2 rounded-lg">
            <svg
              className="w-6 h-6 text-white"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">VAREX <span className="text-indigo-600 dark:text-indigo-400">DriftGuard</span></h1>
        </div>
        <DriftDashboard />
      </div>
    </main>
  );
}

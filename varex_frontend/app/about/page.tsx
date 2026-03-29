import FounderSection from "@/components/FounderSection";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "About Us | VAREX",
  description: "Learn more about VAREX, our foundational philosophy, and our leadership.",
};

export default function AboutPage() {
  return (
    <main className="flex flex-col min-h-screen pt-24 pb-16 px-4 md:px-8">
      <div className="max-w-6xl mx-auto w-full">
        <FounderSection />
      </div>
    </main>
  );
}

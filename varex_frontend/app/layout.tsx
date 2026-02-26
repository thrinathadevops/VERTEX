import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "VAREX – Virtual Architecture, Resilience & Execution",
  description:
    "Engineering & Talent Acceleration firm for DevSecOps, Cybersecurity, SAP SD, and AI-powered hiring.",
  metadataBase: new URL("https://varextech.in"),
  icons: {
    icon:     "/favicon-varex.svg",
    shortcut: "/favicon-varex.svg",
  },
  openGraph: {
    title:       "VAREX Technologies",
    description: "DevSecOps · Cybersecurity · SAP SD · AI Hiring",
    url:         "https://varextech.in",
    siteName:    "VAREX",
    locale:      "en_IN",
    type:        "website",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-slate-950 text-slate-50 antialiased`}>
        <Navbar />
        <main className="mx-auto max-w-6xl px-4 py-8">
          {children}
        </main>
        <Footer />
      </body>
    </html>
  );
}

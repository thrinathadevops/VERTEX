import { Lexend, Source_Sans_3 } from "next/font/google";
import "./globals.css";
import type { ReactNode } from "react";

const bodyFont = Source_Sans_3({
  subsets: ["latin"],
  variable: "--font-source-sans",
  display: "swap",
});

const headingFont = Lexend({
  weight: ["500", "600", "700", "800"],
  subsets: ["latin"],
  variable: "--font-lexend",
  display: "swap",
});

export const metadata = {
  title: "VAREX AI Interview – Assess. Evaluate. Excel.",
  description:
    "AI-powered technical interview platform by VAREX. Free mock interviews, paid practice sessions, and real company assessments for DevSecOps, Cloud, and SRE roles.",
  icons: { icon: "/favicon.ico" },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className={`${bodyFont.variable} ${headingFont.variable}`}>
      <body className="font-body bg-background text-text antialiased selection:bg-cta selection:text-white">
        {children}
      </body>
    </html>
  );
}

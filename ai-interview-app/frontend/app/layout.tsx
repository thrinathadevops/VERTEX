import "./globals.css";
import type { ReactNode } from "react";

export const metadata = {
  title: "VAREX AI Interview – Assess. Evaluate. Excel.",
  description:
    "AI-powered technical interview platform by VAREX. Free mock interviews, paid practice sessions, and real company assessments for DevSecOps, Cloud, and SRE roles.",
  icons: { icon: "/favicon.ico" },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

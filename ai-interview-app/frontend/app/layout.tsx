import { Open_Sans, Poppins } from "next/font/google";
import "./globals.css";
import type { ReactNode } from "react";

const openSans = Open_Sans({
  subsets: ["latin"],
  variable: "--font-open-sans",
  display: "swap",
});

const poppins = Poppins({
  weight: ["400", "500", "600", "700", "900"],
  subsets: ["latin"],
  variable: "--font-poppins",
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
    <html lang="en" className={`${openSans.variable} ${poppins.variable}`}>
      <body className="font-body bg-background text-text antialiased selection:bg-cta selection:text-white">
        {children}
      </body>
    </html>
  );
}

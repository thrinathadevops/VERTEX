// PATH: varex-frontend/tailwind.config.ts
import type { Config } from "tailwindcss";
import typography from "@tailwindcss/typography";
import forms from "@tailwindcss/forms";
import animate from "tailwindcss-animate";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  "#f0f9ff",
          100: "#e0f2fe",
          400: "#38bdf8",
          500: "#0ea5e9",   // primary sky-500
          600: "#0284c7",
          900: "#0c4a6e",
        },
        surface: {
          DEFAULT: "#0f172a",  // slate-900
          card:    "#1e293b",  // slate-800
          border:  "#334155",  // slate-700
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      typography: (theme: (arg: string) => string) => ({
        invert: {
          css: {
            "--tw-prose-body":       theme("colors.slate[300]"),
            "--tw-prose-headings":   theme("colors.slate[100]"),
            "--tw-prose-links":      theme("colors.sky[400]"),
            "--tw-prose-code":       theme("colors.sky[300]"),
            "--tw-prose-pre-bg":     theme("colors.slate[900]"),
          },
        },
      }),
      animation: {
        "in": "fadeIn 0.2s ease-out",
        "slide-in-from-bottom-4": "slideInBottom 0.3s ease-out",
      },
      keyframes: {
        fadeIn: {
          "0%":   { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideInBottom: {
          "0%":   { transform: "translateY(16px)", opacity: "0" },
          "100%": { transform: "translateY(0)",    opacity: "1" },
        },
      },
    },
  },
  plugins: [typography, forms, animate],
};

export default config;

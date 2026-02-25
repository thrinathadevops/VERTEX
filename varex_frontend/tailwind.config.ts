
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        varex: {
          blue: "#1C64F2",
          dark: "#020617",
        },
      },
    },
  },
  plugins: [],
};

export default config;

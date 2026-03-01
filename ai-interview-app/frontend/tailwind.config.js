/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./app/**/*.{js,ts,jsx,tsx,mdx}",
        "./pages/**/*.{js,ts,jsx,tsx,mdx}",
        "./components/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    theme: {
        extend: {
            colors: {
                background: "#020617",
                primary: "#0F172A",
                secondary: "#334155",
                cta: "#0369A1",
                text: "#E2E8F0",
            },
            fontFamily: {
                heading: ["var(--font-lexend)"],
                body: ["var(--font-source-sans)"],
            },
        },
    },
    plugins: [],
}

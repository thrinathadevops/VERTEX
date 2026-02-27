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
                background: "#F8FAFC",
                primary: "#0F172A",
                secondary: "#334155",
                cta: "#0369A1",
                text: "#020617",
            },
            fontFamily: {
                heading: ["var(--font-poppins)"],
                body: ["var(--font-open-sans)"],
            },
        },
    },
    plugins: [],
}

import type { Config } from "tailwindcss";

// Token names below map 1:1 to design-tokens.json (the "Qcells Gradient" theme).
const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        bg: "var(--bg)",
        surface: "var(--surface)",
        "surface-2": "var(--surface-2)",
        text: "var(--text)",
        "text-dim": "var(--text-dim)",
        border: "var(--border)",
        accent: "var(--accent)",
        "accent-ink": "var(--accent-ink)",
        "accent-soft": "var(--accent-soft)",
        "accent-2": "var(--accent-2)",
        "accent-2-soft": "var(--accent-2-soft)",
        danger: "var(--danger)",
        "danger-soft": "var(--danger-soft)",
      },
      fontFamily: {
        display: ["var(--font-display)", "Poppins", "sans-serif"],
        body: ["var(--font-body)", "Inter", "sans-serif"],
        mono: ["var(--font-mono)", "IBM Plex Mono", "monospace"],
      },
      fontSize: {
        xs: "10.5px",
        sm: "11.5px",
        base: "12.5px",
        md: "13.5px",
        lg: "15px",
        xl: "18px",
        "2xl": "22px",
        "3xl": "24px",
        "4xl": "32px",
      },
      borderRadius: {
        sm: "8px",
        md: "14px",
        lg: "20px",
        pill: "999px",
      },
      boxShadow: {
        default: "0 20px 44px -18px rgba(30,111,235,.18)",
        composerFloat: "0 6px 20px -10px rgba(0,0,0,.15)",
      },
      backgroundImage: {
        "brand-gradient": "linear-gradient(120deg, #22C3A6, #1E6FEB)",
      },
      maxWidth: {
        chat: "620px",
      },
      spacing: {
        sidebar: "232px",
      },
    },
  },
  plugins: [],
};

export default config;

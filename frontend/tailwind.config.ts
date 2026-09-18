import type { Config } from "tailwindcss";

// Every color/radius/shadow token here resolves through a CSS custom
// property (see src/app/globals.css's [data-theme="gradient"] block), never
// a hardcoded value — so these Tailwind utilities work unchanged for
// whichever theme is active (src/lib/theme.ts). Token names map 1:1 to
// design-tokens.json (the "Qcells Gradient" theme).
const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      // Sidebar collapses to a mobile drawer below this width — matches the
      // tablet breakpoint already baked into qcells-l1-assistant-mockups.html.
      screens: {
        nav: "900px",
      },
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
        sm: "var(--radius-s)",
        md: "var(--radius-m)",
        lg: "var(--radius-l)",
        pill: "999px",
      },
      boxShadow: {
        default: "var(--shadow)",
        // Not themed in the source mockup — identical across all 5 concepts.
        composerFloat: "0 6px 20px -10px rgba(0,0,0,.15)",
      },
      backgroundImage: {
        "brand-gradient": "var(--grad)",
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

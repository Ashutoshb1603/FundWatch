/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        surface: "#FAF8F4",
        panel: "#FFFFFF",
        rule: "#E4DFD5",
        ink: "#1B1B18",
        muted: "#6B675D",
        accent: { DEFAULT: "#1F5C4D", soft: "#E6EFEC", deep: "#143F35" },
        gold: "#D9A441",
        up: "#1F6F4A",
        down: "#A8412C",
        high: "#B4472F",
        medium: "#B7791F",
        low: "#9A968B",
      },
      fontFamily: {
        sans: ["Inter Variable", "system-ui", "sans-serif"],
        serif: ["Source Serif 4 Variable", "Georgia", "serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};

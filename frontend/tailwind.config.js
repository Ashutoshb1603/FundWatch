/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: "#0F1B2B",
          light: "#16273D",
          border: "#26364B",
        },
        paper: "#F6F3EC",
        gold: "#C9A227",
        teal: "#4F8F82",
        rust: "#B0503A",
        slate: {
          400: "#8B96A5",
          500: "#6B7280",
        },
      },
      fontFamily: {
        serif: ["'Source Serif 4'", "Georgia", "serif"],
        mono: ["'IBM Plex Mono'", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};

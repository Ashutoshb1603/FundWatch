export default function Logo({ tone = "dark" }: { tone?: "dark" | "light" }) {
  const light = tone === "light";
  return (
    <span
      className={`inline-flex items-center gap-2.5 font-serif text-xl font-semibold tracking-tight ${
        light ? "text-white" : "text-ink"
      }`}
    >
      <svg width="26" height="26" viewBox="0 0 28 28" fill="none" aria-hidden>
        <rect x="1.5" y="1.5" width="25" height="25" rx="6" fill={light ? "#FFFFFF" : "#1F5C4D"} />
        <path
          d="M7.5 18.5 12 13.5l3.2 3.1L20.5 9.5"
          stroke={light ? "#143F35" : "#FFFFFF"}
          strokeWidth="2.2"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <circle cx="20.5" cy="9.5" r="2.2" fill="#D9A441" />
      </svg>
      FundWatch
    </span>
  );
}

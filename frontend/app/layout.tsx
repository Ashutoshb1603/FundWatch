import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FundWatch — Disclosure Intelligence",
  description: "Evidence-first mutual fund disclosure intelligence.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}

import { JetBrains_Mono, Space_Grotesk } from "next/font/google";
import "./globals.css";

const displayFont = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-display",
});

const monoFont = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
});

export const metadata = {
  title: "AI Startup Builder",
  description: "Generate startup strategy, market analysis, and deployment links from one idea.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className={`${displayFont.variable} ${monoFont.variable}`}>
        <div className="ambient-ring ambient-ring-a" />
        <div className="ambient-ring ambient-ring-b" />
        <div className="page-shell">{children}</div>
      </body>
    </html>
  );
}

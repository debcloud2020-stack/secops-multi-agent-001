import type { Metadata } from "next";
import { Geist_Mono, Inter, Space_Grotesk } from "next/font/google";
import "./globals.css";

import { Toaster } from "@/components/ui/sonner";

// Self-hosted (next/font) fallbacks — always available in the static export.
const inter = Inter({ variable: "--font-inter", subsets: ["latin"] });
const spaceGrotesk = Space_Grotesk({ variable: "--font-space-grotesk", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });

export const metadata: Metadata = {
  title: "SecOps Multi-Agent",
  description:
    "A multi-agent cybersecurity demo: five specialist agents coordinated by a LangGraph supervisor, with agentic RAG, a prompt-injection guardrail, memory, and cost optimization.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`dark ${inter.variable} ${spaceGrotesk.variable} ${geistMono.variable} h-full antialiased`}
    >
      <head>
        {/* Premium pairing (Clash Grotesk + Satoshi) loaded at runtime; falls back to the
            self-hosted Space Grotesk / Inter above if Fontshare is unreachable. */}
        <link
          rel="stylesheet"
          href="https://api.fontshare.com/v2/css?f[]=clash-grotesk@500,600,700&f[]=satoshi@400,500,700&display=swap"
        />
      </head>
      <body className="relative min-h-full flex flex-col">
        <div aria-hidden className="bg-grid-overlay pointer-events-none fixed inset-0 -z-10" />
        {children}
        <Toaster richColors position="top-right" />
      </body>
    </html>
  );
}

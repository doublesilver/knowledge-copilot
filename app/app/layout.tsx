import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Knowledge Copilot",
  description: "AI document copilot with RAG-based Q&A, actions, and metrics tracking",
  openGraph: {
    title: "Knowledge Copilot",
    description: "AI document copilot with RAG-based Q&A, actions, and metrics tracking",
    type: "website",
    locale: "ko_KR",
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  );
}

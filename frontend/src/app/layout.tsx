import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Parallax — Graduate admissions review",
  description: "AI-powered graduate student outreach review for university faculty.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full">
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}

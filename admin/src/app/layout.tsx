import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DogeAPI Admin",
  description: "DogeAPI super-admin portal",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className="min-h-screen bg-background text-foreground antialiased"
        suppressHydrationWarning
      >
        {children}
      </body>
    </html>
  );
}

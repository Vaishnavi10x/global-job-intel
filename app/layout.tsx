import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Job Market Dashboard",
  description: "Global Job Intelligence",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-slate-950 m-0 p-0 overflow-x-hidden">
        {children}
      </body>
    </html>
  );
}
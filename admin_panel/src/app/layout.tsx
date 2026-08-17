import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Tozalash Servis - AI Admin Panel",
  description: "Aqlli tozalash servisi boshqaruv tizimi",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="uz" className="dark">
      <body className={`${inter.className} antialiased text-slate-100 bg-slate-900`}>
        {children}
      </body>
    </html>
  );
}

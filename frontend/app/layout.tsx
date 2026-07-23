import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Link from "next/link";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Echo Solar — Call-to-quote for solar sales",
  description:
    "Turn a live sales call into a solar installation quote — transcription, extraction, and PDF generation in one flow.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased bg-white`}>
        <nav className="border-b border-gray-100">
          <div className="max-w-2xl mx-auto px-4 py-4 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2 font-semibold text-gray-900">
              <span className="flex items-end gap-[2px] h-3" aria-hidden="true">
                {[0, 1, 2].map((i) => (
                  <span
                    key={i}
                    className="waveform-bar w-[2px] h-full bg-green-500 rounded-full"
                    style={{ animationDelay: `${i * 0.15}s` }}
                  />
                ))}
              </span>
              Echo Solar
            </Link>
            <div className="flex gap-6 text-sm font-medium text-gray-600">
              <Link href="/" className="hover:text-gray-900 transition-colors">Live Call</Link>
              <Link href="/calculator" className="hover:text-gray-900 transition-colors">Calculator</Link>
            </div>
          </div>
        </nav>
        <main>{children}</main>
        <footer className="border-t border-gray-100 mt-16">
          <div className="max-w-2xl mx-auto px-4 py-6 text-center text-xs text-gray-400">
            &copy; {new Date().getFullYear()} Echo Solar
          </div>
        </footer>
      </body>
    </html>
  );
}
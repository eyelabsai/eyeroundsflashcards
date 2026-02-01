import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "EyeRounds Flashcards",
  description: "Ophthalmology flashcard study app with oral boards preparation",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
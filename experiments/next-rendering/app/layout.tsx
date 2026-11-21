import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./styles.css";

export const metadata: Metadata = {
  title: "Mindgarden | Rendering lab",
  description: "Compare Next.js build-time rendering, request-time rendering, and browser interaction using a fictional garden.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

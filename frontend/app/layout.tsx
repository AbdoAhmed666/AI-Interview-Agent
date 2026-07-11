import type { Metadata } from "next";
import "./globals.css";
import { InterviewProvider } from "@/contexts/InterviewContext";
import { AuthProvider } from "@/contexts/AuthContext";
import { Toaster } from "sonner";

export const metadata: Metadata = {
  title: "AI Interview Agent",
  description: "Production-grade AI Technical Interview Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <InterviewProvider>
            <Toaster
              position="top-right"
              richColors
            />
            {children}
          </InterviewProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
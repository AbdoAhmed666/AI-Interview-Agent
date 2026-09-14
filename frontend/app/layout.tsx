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
    // Browser extensions commonly inject attributes onto <html>/<body> before
    // React hydrates (e.g. bbai-tooltip-injected), which React would otherwise
    // report as a hydration mismatch. suppressHydrationWarning applies to the
    // element itself only, so the rest of the tree is still checked.
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>
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
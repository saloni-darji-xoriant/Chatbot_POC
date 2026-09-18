import type { Metadata } from "next";

import { AuthProvider } from "@/context/AuthContext";
import { ChatProvider } from "@/context/ChatContext";
import { ACTIVE_THEME } from "@/lib/theme";
import "./globals.css";

export const metadata: Metadata = {
  title: "Qcells L1 Assistant",
  description: "Hanwha Qcells L1 support assistant for installers and admins",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" data-theme={ACTIVE_THEME}>
      <body className="font-body">
        <AuthProvider>
          <ChatProvider>{children}</ChatProvider>
        </AuthProvider>
      </body>
    </html>
  );
}

"use client";

import { Lock } from "lucide-react";

import { usePassword } from "@/components/providers/password-provider";

/** Renders dashboard content only once the demo password is set (avoids premature 401s). */
export function AuthGate({ children }: { children: React.ReactNode }) {
  const { authed } = usePassword();
  if (!authed) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-3 p-10 text-center text-muted-foreground">
        <Lock className="size-8" />
        <p>Enter the demo password to view the dashboard.</p>
      </div>
    );
  }
  return <>{children}</>;
}

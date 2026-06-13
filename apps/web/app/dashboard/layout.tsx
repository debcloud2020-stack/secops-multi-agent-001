import { AuthGate } from "@/components/dashboard/auth-gate";
import { DashboardNav } from "@/components/dashboard/nav";
import { PasswordProvider } from "@/components/providers/password-provider";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <PasswordProvider>
      <div className="flex flex-1 flex-col md:flex-row">
        <DashboardNav />
        <main className="flex flex-1 flex-col">
          <AuthGate>{children}</AuthGate>
        </main>
      </div>
    </PasswordProvider>
  );
}

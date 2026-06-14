import { DashboardNav } from "@/components/dashboard/nav";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-1 flex-col md:flex-row">
      <DashboardNav />
      <main className="flex flex-1 flex-col">{children}</main>
    </div>
  );
}

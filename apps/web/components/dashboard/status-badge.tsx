import { Badge } from "@/components/ui/badge";
import { STATUS_CLASS, STATUS_LABEL } from "@/lib/format";
import type { RunStatusValue } from "@/lib/types";
import { cn } from "@/lib/utils";

export function StatusBadge({ status }: { status: RunStatusValue }) {
  return (
    <Badge
      variant="outline"
      className={cn("font-medium", STATUS_CLASS[status], status === "running" && "animate-pulse")}
    >
      {STATUS_LABEL[status]}
    </Badge>
  );
}

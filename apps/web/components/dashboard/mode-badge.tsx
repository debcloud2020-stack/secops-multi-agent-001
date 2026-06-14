import { Badge } from "@/components/ui/badge";
import { MODE_ACCENT, MODE_LABEL } from "@/lib/format";
import type { DataMode } from "@/lib/types";
import { cn } from "@/lib/utils";

/** Colored badge naming the data mode (slate=mock, emerald=live, violet=synthetic). */
export function ModeBadge({ mode }: { mode: DataMode }) {
  return (
    <Badge variant="outline" className={cn("font-medium", MODE_ACCENT[mode].badge)}>
      {MODE_LABEL[mode]}
    </Badge>
  );
}

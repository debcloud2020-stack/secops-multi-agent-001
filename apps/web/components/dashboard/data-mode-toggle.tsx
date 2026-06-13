"use client";

import { Button } from "@/components/ui/button";
import type { DataMode } from "@/lib/types";
import { cn } from "@/lib/utils";

const MODES: { value: DataMode; label: string; enabled: boolean }[] = [
  { value: "mock", label: "Mock", enabled: true },
  { value: "live", label: "Live", enabled: false },
  { value: "synthetic", label: "Synthetic", enabled: false },
];

export function DataModeToggle({
  value,
  onChange,
}: {
  value: DataMode;
  onChange: (m: DataMode) => void;
}) {
  return (
    <div className="inline-flex rounded-lg border p-0.5">
      {MODES.map((m) => (
        <Button
          key={m.value}
          type="button"
          size="sm"
          variant="ghost"
          disabled={!m.enabled}
          title={m.enabled ? undefined : "Available in a later phase"}
          onClick={() => onChange(m.value)}
          className={cn(
            "h-7 rounded-md px-3 text-xs",
            value === m.value && "bg-secondary text-secondary-foreground",
          )}
        >
          {m.label}
          {!m.enabled && <span className="ml-1 text-[10px] text-muted-foreground">P5</span>}
        </Button>
      ))}
    </div>
  );
}

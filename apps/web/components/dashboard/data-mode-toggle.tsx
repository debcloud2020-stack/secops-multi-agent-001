"use client";

import { Button } from "@/components/ui/button";
import type { DataMode } from "@/lib/types";
import { cn } from "@/lib/utils";

const MODES: { value: DataMode; label: string; hint: string }[] = [
  { value: "mock", label: "Mock", hint: "Offline fixtures (default)" },
  { value: "live", label: "Live", hint: "Real Azure telemetry; falls back to mock without creds" },
  { value: "synthetic", label: "Synthetic", hint: "Synthetic custom table; falls back to mock without creds" },
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
          title={m.hint}
          onClick={() => onChange(m.value)}
          className={cn(
            "h-7 rounded-md px-3 text-xs",
            value === m.value && "bg-secondary text-secondary-foreground",
          )}
        >
          {m.label}
        </Button>
      ))}
    </div>
  );
}

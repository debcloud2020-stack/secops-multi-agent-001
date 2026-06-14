import { cn } from "@/lib/utils";

/** Color bands for a CVSS base score (0–10), per the functional accent palette. */
function band(score: number): { stroke: string; text: string; label: string } {
  if (score >= 9) return { stroke: "#f87171", text: "text-red-300", label: "Critical" };
  if (score >= 7) return { stroke: "#fb923c", text: "text-orange-300", label: "High" };
  if (score >= 4) return { stroke: "#fbbf24", text: "text-amber-300", label: "Medium" };
  return { stroke: "#22d3ee", text: "text-cyan-300", label: "Low" };
}

/**
 * Circular CVSS risk gauge driven by real cve_matches data (e.g. Log4Shell 9.83).
 * The arc fills proportionally to score/10; color follows the CVSS severity band.
 */
export function CvssGauge({
  score,
  cveId,
  size = 132,
}: {
  score: number;
  cveId?: string;
  size?: number;
}) {
  const clamped = Math.max(0, Math.min(10, score));
  const stroke = 10;
  const r = (size - stroke) / 2;
  const c = 2 * Math.PI * r;
  const offset = c * (1 - clamped / 10);
  const { stroke: color, text, label } = band(clamped);

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke="rgba(255,255,255,0.08)"
            strokeWidth={stroke}
          />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            fill="none"
            stroke={color}
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={c}
            strokeDashoffset={offset}
            style={{ transition: "stroke-dashoffset 700ms ease-out", filter: `drop-shadow(0 0 6px ${color}80)` }}
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={cn("font-heading text-3xl font-semibold tabular-nums", text)}>
            {clamped.toFixed(clamped % 1 === 0 ? 0 : 2)}
          </span>
          <span className="text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
            CVSS
          </span>
        </div>
      </div>
      <div className="text-center">
        <p className={cn("text-xs font-semibold", text)}>{label} risk</p>
        {cveId && <p className="font-mono text-[11px] text-muted-foreground">{cveId}</p>}
      </div>
    </div>
  );
}

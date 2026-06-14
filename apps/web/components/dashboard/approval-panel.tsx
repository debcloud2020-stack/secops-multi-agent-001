"use client";

import { Check, X } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import type { Decision } from "@/lib/types";

export function ApprovalPanel({
  onDecision,
}: {
  onDecision: (decision: Decision, editedPlan?: string | null) => void | Promise<void>;
}) {
  const [editedPlan, setEditedPlan] = useState("");
  const [busy, setBusy] = useState(false);

  async function decide(decision: Decision) {
    setBusy(true);
    await onDecision(decision, decision === "approve" && editedPlan.trim() ? editedPlan : null);
    setBusy(false);
  }

  return (
    <Card className="border-amber-500/40 bg-amber-500/10 ring-1 ring-amber-500/20">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-base text-amber-200">
          <span className="size-2 animate-pulse rounded-full bg-amber-400 text-amber-400 shadow-[0_0_8px_currentColor]" />
          Approval required
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm text-muted-foreground">
          The incident-response plan needs human sign-off before its steps are executed. You can
          approve as-is, edit the plan, or reject (the steps will not run).
        </p>
        <div className="space-y-1.5">
          <Label htmlFor="edited-plan">Edited plan (optional)</Label>
          <Textarea
            id="edited-plan"
            placeholder="Leave blank to approve the proposed plan unchanged…"
            value={editedPlan}
            onChange={(e) => setEditedPlan(e.target.value)}
            rows={4}
          />
        </div>
        <div className="flex gap-2">
          <Button onClick={() => decide("approve")} disabled={busy}>
            <Check className="size-4" /> Approve
          </Button>
          <Button variant="destructive" onClick={() => decide("reject")} disabled={busy}>
            <X className="size-4" /> Reject
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

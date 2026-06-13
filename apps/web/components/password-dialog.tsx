"use client";

import { ShieldCheck } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function PasswordDialog({
  open,
  onSubmit,
}: {
  open: boolean;
  onSubmit: (pw: string) => Promise<boolean>;
}) {
  const [value, setValue] = useState("");
  const [error, setError] = useState(false);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!value || busy) return;
    setBusy(true);
    setError(false);
    const ok = await onSubmit(value);
    setBusy(false);
    if (!ok) {
      setError(true);
      setValue("");
    }
  }

  return (
    <Dialog open={open}>
      <DialogContent showCloseButton={false}>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <ShieldCheck className="size-5 text-primary" />
            Demo access
          </DialogTitle>
          <DialogDescription>
            Enter the demo password to open the SecOps dashboard. It is sent only to your
            local API and stored for this browser tab.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="demo-password">Password</Label>
            <Input
              id="demo-password"
              type="password"
              autoFocus
              value={value}
              onChange={(e) => setValue(e.target.value)}
              aria-invalid={error}
            />
            {error && (
              <p className="text-sm text-destructive">
                Incorrect password (or the API is not running).
              </p>
            )}
          </div>
          <Button type="submit" className="w-full" disabled={busy || !value}>
            {busy ? "Checking…" : "Unlock"}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}

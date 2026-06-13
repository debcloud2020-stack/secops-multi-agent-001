"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";

import { PasswordDialog } from "@/components/password-dialog";
import { checkHealth, clearPassword, getPassword, setPassword } from "@/lib/api";

interface PasswordCtx {
  authed: boolean;
  reauth: () => void;
}

const Ctx = createContext<PasswordCtx>({ authed: false, reauth: () => {} });

export function usePassword() {
  return useContext(Ctx);
}

/**
 * Gates the dashboard behind the demo password. Shows a one-time modal when no valid
 * password is stored; a 401 anywhere can call `reauth()` to clear and re-prompt.
 */
export function PasswordProvider({ children }: { children: React.ReactNode }) {
  // `checked` flips true once we've read sessionStorage on the client (avoids a dialog
  // flash before hydration); `authed` reflects whether a password is stored.
  const [state, setState] = useState({ authed: false, checked: false });

  useEffect(() => {
    // One-shot read of the stored password (client-only external store) on mount.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setState({ authed: Boolean(getPassword()), checked: true });
  }, []);

  const reauth = useCallback(() => {
    clearPassword();
    setState((s) => ({ ...s, authed: false }));
  }, []);

  const submit = useCallback(async (pw: string): Promise<boolean> => {
    setPassword(pw);
    try {
      await checkHealth();
      setState((s) => ({ ...s, authed: true }));
      return true;
    } catch {
      clearPassword();
      return false;
    }
  }, []);

  const { authed, checked } = state;

  return (
    <Ctx.Provider value={{ authed, reauth }}>
      {children}
      <PasswordDialog open={checked && !authed} onSubmit={submit} />
    </Ctx.Provider>
  );
}

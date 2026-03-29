"use client";

import { useState } from "react";
import { login, setToken, TOKEN_KEY } from "@/lib/api";

export default function LoginBar({ onAuth }: { onAuth: () => void }) {
  const [u, setU] = useState("testuser");
  const [p, setP] = useState("password123");
  const [err, setErr] = useState("");
  const [authed, setAuthed] = useState(() => {
    if (typeof window === "undefined") return false;
    return !!localStorage.getItem(TOKEN_KEY);
  });

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    setErr("");
    try {
      await login(u, p);
      setAuthed(true);
      onAuth();
    } catch {
      setErr("Invalid credentials");
    }
  }

  function logout() {
    setToken(null);
    setAuthed(false);
    onAuth();
  }

  return (
    <form onSubmit={handleLogin} className="flex flex-wrap items-center gap-2 text-sm">
      {authed ? (
        <button
          type="button"
          onClick={logout}
          className="px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-600 text-slate-200 hover:bg-slate-700"
        >
          Sign out
        </button>
      ) : (
        <>
          <input
            className="bg-slate-800 border border-slate-600 rounded px-2 py-1 text-white w-28"
            value={u}
            onChange={(e) => setU(e.target.value)}
            placeholder="user"
          />
          <input
            type="password"
            className="bg-slate-800 border border-slate-600 rounded px-2 py-1 text-white w-28"
            value={p}
            onChange={(e) => setP(e.target.value)}
            placeholder="password"
          />
          <button
            type="submit"
            className="px-3 py-1.5 rounded-lg bg-indigo-600 text-white font-medium hover:bg-indigo-500"
          >
            Sign in
          </button>
        </>
      )}
      {err && <span className="text-red-400 text-xs">{err}</span>}
    </form>
  );
}

"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";

import { api, clearToken } from "@/lib/api";
import { logoutOneSignal } from "@/lib/onesignal";
import type { User } from "@/lib/types";

export function AppHeader({ user }: { user: User }) {
  const pathname = usePathname();
  const router = useRouter();
  const [loggingOut, setLoggingOut] = useState(false);

  async function logout() {
    setLoggingOut(true);
    try {
      await api<void>("/auth/logout/", { method: "POST" });
      await logoutOneSignal();
    } catch {
      // The local token must still be cleared if the server is unreachable.
    } finally {
      clearToken();
      router.replace("/");
    }
  }

  return (
    <header className="app-header">
      <Link className="brand" href="/dashboard" aria-label="SignalDesk dashboard">
        <span className="brand-mark">S</span>
        <span>SignalDesk</span>
      </Link>
      <nav className="app-nav" aria-label="Primary navigation">
        <Link
          className={pathname === "/dashboard" ? "active" : ""}
          href="/dashboard"
        >
          My notifications
        </Link>
        {user.is_staff && (
          <Link
            className={pathname.startsWith("/admin") ? "active" : ""}
            href="/admin/notifications"
          >
            Notification settings
          </Link>
        )}
      </nav>
      <div className="header-user">
        <span className="avatar">
          {(user.first_name || user.username).slice(0, 1).toUpperCase()}
        </span>
        <span className="user-copy">
          <strong>{user.first_name || user.username}</strong>
          <small>{user.is_staff ? "Administrator" : "Member"}</small>
        </span>
        <button
          className="button button-ghost button-small"
          disabled={loggingOut}
          onClick={logout}
          type="button"
        >
          {loggingOut ? "Signing out…" : "Sign out"}
        </button>
      </div>
    </header>
  );
}

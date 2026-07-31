"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { api, getToken, saveToken } from "@/lib/api";
import type { User } from "@/lib/types";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("AdminPass123!");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!getToken()) return;
    api<User>("/auth/me/")
      .then((user) =>
        router.replace(user.is_staff ? "/admin/notifications" : "/dashboard"),
      )
      .catch(() => undefined);
  }, [router]);

  function chooseDemo(role: "admin" | "member") {
    if (role === "admin") {
      setUsername("admin");
      setPassword("AdminPass123!");
    } else {
      setUsername("demo");
      setPassword("UserPass123!");
    }
    setError("");
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      const result = await api<{ token: string; user: User }>("/auth/login/", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      });
      saveToken(result.token);
      router.replace(
        result.user.is_staff ? "/admin/notifications" : "/dashboard",
      );
    } catch (loginError) {
      setError(
        loginError instanceof Error ? loginError.message : "Unable to sign in.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <main className="login-layout">
      <section className="login-story">
        <div>
          <div className="brand brand-on-dark">
            <span className="brand-mark">S</span>
            <span>SignalDesk</span>
          </div>
          <div className="eyebrow eyebrow-dark">Notification operations</div>
          <h1>Every message.<br />One calm workspace.</h1>
          <p className="login-lede">
            Create, test, and control WhatsApp, email, and browser notifications
            without jumping between provider dashboards.
          </p>
        </div>
        <div className="channel-strip">
          <div>
            <span className="channel-dot whatsapp" />
            <strong>WhatsApp</strong>
            <small>Cloud API</small>
          </div>
          <div>
            <span className="channel-dot email" />
            <strong>Email</strong>
            <small>Postmark</small>
          </div>
          <div>
            <span className="channel-dot push" />
            <strong>Web Push</strong>
            <small>OneSignal</small>
          </div>
        </div>
      </section>

      <section className="login-panel">
        <div className="login-card">
          <div className="eyebrow">Welcome back</div>
          <h2>Sign in to the demo</h2>
          <p>
            A successful sign-in fires the Login notification trigger.
          </p>

          <div className="demo-switch" aria-label="Choose demo account">
            <button
              className={username === "admin" ? "active" : ""}
              onClick={() => chooseDemo("admin")}
              type="button"
            >
              Admin demo
            </button>
            <button
              className={username === "demo" ? "active" : ""}
              onClick={() => chooseDemo("member")}
              type="button"
            >
              Member demo
            </button>
          </div>

          <form onSubmit={submit}>
            <label className="field">
              <span>Username</span>
              <input
                autoComplete="username"
                onChange={(event) => setUsername(event.target.value)}
                required
                value={username}
              />
            </label>
            <label className="field">
              <span>Password</span>
              <input
                autoComplete="current-password"
                onChange={(event) => setPassword(event.target.value)}
                required
                type="password"
                value={password}
              />
            </label>
            {error && <div className="form-alert error">{error}</div>}
            <button
              className="button button-primary button-wide"
              disabled={submitting}
              type="submit"
            >
              {submitting ? "Signing in…" : "Sign in and fire trigger"}
            </button>
          </form>

          <div className="login-note">
            <span className="status-pip success" />
            Provider calls run safely in mock mode until sandbox keys are added.
          </div>
        </div>
      </section>
    </main>
  );
}

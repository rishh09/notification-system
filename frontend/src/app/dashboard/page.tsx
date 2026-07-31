"use client";

import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useMemo, useState } from "react";

import { AppHeader } from "@/components/app-header";
import { LoadingScreen } from "@/components/loading-screen";
import { api, clearToken } from "@/lib/api";
import { subscribeBrowser } from "@/lib/onesignal";
import type { PushSubscription, User } from "@/lib/types";

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [subscriptions, setSubscriptions] = useState<PushSubscription[]>([]);
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [subscribing, setSubscribing] = useState(false);

  useEffect(() => {
    Promise.all([
      api<User>("/auth/me/"),
      api<PushSubscription[]>("/push/subscriptions/"),
    ])
      .then(([loadedUser, loadedSubscriptions]) => {
        setUser(loadedUser);
        setEmail(
          loadedUser.notification_profile.notification_email ||
            loadedUser.email,
        );
        setPhone(loadedUser.notification_profile.whatsapp_phone);
        setSubscriptions(loadedSubscriptions);
      })
      .catch(() => {
        clearToken();
        router.replace("/");
      });
  }, [router]);

  const activeSubscriptions = useMemo(
    () => subscriptions.filter((subscription) => subscription.is_active),
    [subscriptions],
  );

  async function saveProfile(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError("");
    setNotice("");
    try {
      const profile = await api<User["notification_profile"]>(
        "/auth/profile/",
        {
          method: "PATCH",
          body: JSON.stringify({
            notification_email: email,
            whatsapp_phone: phone,
          }),
        },
      );
      setUser((current) =>
        current ? { ...current, notification_profile: profile } : current,
      );
      setNotice("Notification destinations saved.");
    } catch (saveError) {
      setError(
        saveError instanceof Error ? saveError.message : "Unable to save.",
      );
    } finally {
      setSaving(false);
    }
  }

  async function subscribe() {
    if (!user) return;
    setSubscribing(true);
    setError("");
    setNotice("");
    try {
      const subscriptionId = process.env.NEXT_PUBLIC_ONESIGNAL_APP_ID
        ? await subscribeBrowser(user.id)
        : `demo-browser-${user.id}`;
      const saved = await api<PushSubscription>("/push/subscriptions/", {
        method: "POST",
        body: JSON.stringify({
          subscription_id: subscriptionId,
          device_label: process.env.NEXT_PUBLIC_ONESIGNAL_APP_ID
            ? "Current browser"
            : "Mock browser",
          is_active: true,
        }),
      });
      setSubscriptions((current) => [
        saved,
        ...current.filter((item) => item.id !== saved.id),
      ]);
      setNotice(
        process.env.NEXT_PUBLIC_ONESIGNAL_APP_ID
          ? "This browser is ready for Web Push."
          : "Mock browser subscription saved. Add a OneSignal App ID for real Web Push.",
      );
    } catch (subscribeError) {
      setError(
        subscribeError instanceof Error
          ? subscribeError.message
          : "Unable to subscribe this browser.",
      );
    } finally {
      setSubscribing(false);
    }
  }

  if (!user) return <LoadingScreen />;

  return (
    <div className="app-frame">
      <AppHeader user={user} />
      <main className="page-shell">
        <div className="page-heading">
          <div>
            <div className="eyebrow">Member workspace</div>
            <h1>Ready when your events fire.</h1>
            <p>
              Keep your notification destinations current, then use the site
              normally. Login and Logout are connected to the notification
              engine.
            </p>
          </div>
          <div className="environment-badge">
            <span className="status-pip success" />
            Safe sandbox mode
          </div>
        </div>

        {(notice || error) && (
          <div className={`form-alert ${error ? "error" : "success"}`}>
            {error || notice}
          </div>
        )}

        <section className="summary-grid">
          <article className="summary-card">
            <span className="summary-icon whatsapp">WA</span>
            <div>
              <small>WhatsApp destination</small>
              <strong>{phone || "Not configured"}</strong>
            </div>
            <span className={`status-pill ${phone ? "ready" : "muted"}`}>
              {phone ? "Ready" : "Missing"}
            </span>
          </article>
          <article className="summary-card">
            <span className="summary-icon email">@</span>
            <div>
              <small>Email destination</small>
              <strong>{email || "Not configured"}</strong>
            </div>
            <span className={`status-pill ${email ? "ready" : "muted"}`}>
              {email ? "Ready" : "Missing"}
            </span>
          </article>
          <article className="summary-card">
            <span className="summary-icon push">P</span>
            <div>
              <small>Web Push browsers</small>
              <strong>{activeSubscriptions.length} subscribed</strong>
            </div>
            <span
              className={`status-pill ${
                activeSubscriptions.length ? "ready" : "muted"
              }`}
            >
              {activeSubscriptions.length ? "Ready" : "Missing"}
            </span>
          </article>
        </section>

        <div className="content-grid">
          <section className="panel">
            <div className="panel-heading">
              <div>
                <div className="eyebrow">Delivery profile</div>
                <h2>Where should messages arrive?</h2>
              </div>
              <span className="step-number">01</span>
            </div>
            <form className="stack-form" onSubmit={saveProfile}>
              <label className="field">
                <span>Email address</span>
                <input
                  onChange={(event) => setEmail(event.target.value)}
                  placeholder="you@example.com"
                  type="email"
                  value={email}
                />
                <small>Must be allowed by your Postmark sandbox.</small>
              </label>
              <label className="field">
                <span>WhatsApp phone number</span>
                <input
                  inputMode="tel"
                  onChange={(event) => setPhone(event.target.value)}
                  placeholder="919876543210"
                  value={phone}
                />
                <small>International digits only; add it as a Meta test recipient.</small>
              </label>
              <button
                className="button button-primary"
                disabled={saving}
                type="submit"
              >
                {saving ? "Saving…" : "Save destinations"}
              </button>
            </form>
          </section>

          <section className="panel push-panel">
            <div className="panel-heading">
              <div>
                <div className="eyebrow">Browser channel</div>
                <h2>Subscribe this browser</h2>
              </div>
              <span className="step-number">02</span>
            </div>
            <div className="browser-illustration">
              <div className="browser-top">
                <span />
                <span />
                <span />
              </div>
              <div className="notification-preview">
                <span className="brand-mark">S</span>
                <div>
                  <strong>Welcome back</strong>
                  <p>Your login was successful.</p>
                </div>
                <small>now</small>
              </div>
            </div>
            <p className="panel-copy">
              Permission is requested only after you click. Production Web Push
              uses OneSignal; local work can use the mock subscription.
            </p>
            <button
              className="button button-secondary"
              disabled={subscribing}
              onClick={subscribe}
              type="button"
            >
              {subscribing
                ? "Connecting browser…"
                : activeSubscriptions.length
                  ? "Refresh browser subscription"
                  : "Enable browser notifications"}
            </button>
          </section>
        </div>
      </main>
    </div>
  );
}

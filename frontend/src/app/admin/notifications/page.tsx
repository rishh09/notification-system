"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  EditorTarget,
  TemplateEditor,
  TestSendDialog,
  TriggerDialog,
} from "@/components/admin-dialogs";
import { AppHeader } from "@/components/app-header";
import { LoadingScreen } from "@/components/loading-screen";
import { api, clearToken } from "@/lib/api";
import type {
  Channel,
  Delivery,
  NotificationTemplate,
  Trigger,
  User,
} from "@/lib/types";

const channels: Array<{ key: Channel; label: string; provider: string }> = [
  { key: "whatsapp", label: "WhatsApp", provider: "Cloud API" },
  { key: "email", label: "Email", provider: "Postmark" },
  { key: "web_push", label: "Web Push", provider: "OneSignal" },
];

function statusTone(status: string) {
  if (status === "sent" || status === "approved") return "ready";
  if (status === "failed" || status === "rejected") return "danger";
  if (status === "pending") return "warning";
  return "muted";
}

export default function NotificationSettingsPage() {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [triggers, setTriggers] = useState<Trigger[]>([]);
  const [deliveries, setDeliveries] = useState<Delivery[]>([]);
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const [editor, setEditor] = useState<EditorTarget | null>(null);
  const [testTarget, setTestTarget] =
    useState<NotificationTemplate | null>(null);
  const [showTriggerForm, setShowTriggerForm] = useState(false);
  const [busyId, setBusyId] = useState<number | null>(null);

  const loadData = useCallback(async () => {
    try {
      const [loadedUser, loadedTriggers, loadedDeliveries] = await Promise.all([
        api<User>("/auth/me/"),
        api<Trigger[]>("/admin/triggers/"),
        api<Delivery[]>("/admin/deliveries/"),
      ]);
      if (!loadedUser.is_staff) {
        router.replace("/dashboard");
        return;
      }
      setUser(loadedUser);
      setTriggers(loadedTriggers);
      setDeliveries(loadedDeliveries.slice(0, 12));
    } catch {
      clearToken();
      router.replace("/");
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => {
    const timeout = window.setTimeout(loadData, 0);
    return () => window.clearTimeout(timeout);
  }, [loadData]);

  function flash(message: string, isError = false) {
    setError(isError ? message : "");
    setNotice(isError ? "" : message);
    window.setTimeout(() => {
      setNotice("");
      setError("");
    }, 4500);
  }

  async function toggle(template: NotificationTemplate) {
    setBusyId(template.id);
    try {
      await api(`/admin/templates/${template.id}/toggle/`, {
        method: "POST",
        body: JSON.stringify({ is_enabled: !template.is_enabled }),
      });
      flash(
        `${template.channel_label} ${
          template.is_enabled ? "disabled" : "enabled"
        }.`,
      );
      await loadData();
    } catch (toggleError) {
      flash(
        toggleError instanceof Error ? toggleError.message : "Toggle failed.",
        true,
      );
    } finally {
      setBusyId(null);
    }
  }

  async function whatsappAction(
    template: NotificationTemplate,
    action: "sync" | "status",
  ) {
    setBusyId(template.id);
    try {
      await api(
        `/admin/templates/${template.id}/whatsapp-${
          action === "sync" ? "sync" : "status"
        }/`,
        { method: action === "sync" ? "POST" : "GET" },
      );
      flash(
        action === "sync"
          ? "WhatsApp template submitted for synchronization."
          : "WhatsApp approval status refreshed.",
      );
      await loadData();
    } catch (syncError) {
      flash(
        syncError instanceof Error
          ? syncError.message
          : "Provider request failed.",
        true,
      );
    } finally {
      setBusyId(null);
    }
  }

  const activeChannels = useMemo(
    () =>
      triggers.reduce(
        (count, trigger) =>
          count +
          trigger.templates.filter((template) => template.is_enabled).length,
        0,
      ),
    [triggers],
  );
  const recentFailures = deliveries.filter(
    (delivery) => delivery.status === "failed",
  ).length;

  if (loading || !user) {
    return <LoadingScreen label="Opening Notification Settings…" />;
  }

  return (
    <div className="app-frame">
      <AppHeader user={user} />
      <main className="page-shell page-shell-wide">
        <div className="page-heading admin-heading">
          <div>
            <div className="eyebrow">Admin workspace</div>
            <h1>Notification Settings</h1>
            <p>
              One trigger per row. Create, test, and control every channel from
              this matrix.
            </p>
          </div>
          <button
            className="button button-primary"
            onClick={() => setShowTriggerForm(true)}
            type="button"
          >
            <span aria-hidden="true">＋</span> Add trigger
          </button>
        </div>

        {(notice || error) && (
          <div className={`toast ${error ? "error" : "success"}`}>
            <span
              className={`status-pip ${error ? "danger" : "success"}`}
            />
            {error || notice}
          </div>
        )}

        <section className="admin-stats" aria-label="Notification summary">
          <div>
            <small>Configured triggers</small>
            <strong>{triggers.length}</strong>
            <span>Database-driven events</span>
          </div>
          <div>
            <small>Enabled channels</small>
            <strong>{activeChannels}</strong>
            <span>Across the full matrix</span>
          </div>
          <div>
            <small>Recent failures</small>
            <strong>{recentFailures}</strong>
            <span>From the latest deliveries</span>
          </div>
          <div className="sandbox-stat">
            <small>Provider mode</small>
            <strong>Sandbox</strong>
            <span>
              <span className="status-pip success" /> Safe to test
            </span>
          </div>
        </section>

        <section className="matrix-panel">
          <div className="matrix-toolbar">
            <div>
              <h2>Trigger matrix</h2>
              <p>
                Templates live in the cells where triggers and channels meet.
              </p>
            </div>
            <div className="matrix-legend">
              <span>
                <i className="legend-dot enabled" /> Enabled
              </span>
              <span>
                <i className="legend-dot disabled" /> Disabled
              </span>
              <span>
                <i className="legend-dot missing" /> Missing
              </span>
            </div>
          </div>

          <div className="matrix-scroll">
            <table className="notification-matrix">
              <thead>
                <tr>
                  <th>Trigger</th>
                  {channels.map((channel) => (
                    <th key={channel.key}>
                      <span>{channel.label}</span>
                      <small>{channel.provider}</small>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {triggers.map((trigger) => (
                  <tr key={trigger.id}>
                    <td className="trigger-cell">
                      <div className="trigger-title">
                        <span
                          className={`trigger-mark ${
                            trigger.is_active ? "" : "inactive"
                          }`}
                        >
                          {trigger.name.slice(0, 1)}
                        </span>
                        <div>
                          <strong>{trigger.name}</strong>
                          <code>{trigger.key}</code>
                        </div>
                      </div>
                      <p>{trigger.description || "No description provided."}</p>
                    </td>
                    {channels.map((channel) => {
                      const template = trigger.templates.find(
                        (item) => item.channel === channel.key,
                      );
                      return (
                        <td key={channel.key}>
                          {template ? (
                            <TemplateCell
                              busy={busyId === template.id}
                              onEdit={() =>
                                setEditor({
                                  trigger,
                                  channel: channel.key,
                                  template,
                                })
                              }
                              onProviderAction={() =>
                                whatsappAction(
                                  template,
                                  template.provider_status === "not_synced"
                                    ? "sync"
                                    : "status",
                                )
                              }
                              onTest={() => setTestTarget(template)}
                              onToggle={() => toggle(template)}
                              template={template}
                            />
                          ) : (
                            <button
                              className="empty-cell"
                              onClick={() =>
                                setEditor({
                                  trigger,
                                  channel: channel.key,
                                })
                              }
                              type="button"
                            >
                              <span>＋</span>
                              Create template
                            </button>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        <DeliveryActivity deliveries={deliveries} onRefresh={loadData} />
      </main>

      {editor && (
        <TemplateEditor
          onClose={() => setEditor(null)}
          onSaved={async () => {
            setEditor(null);
            flash("Template saved.");
            await loadData();
          }}
          target={editor}
        />
      )}
      {testTarget && (
        <TestSendDialog
          onClose={() => setTestTarget(null)}
          onSent={async (message) => {
            setTestTarget(null);
            flash(message);
            await loadData();
          }}
          template={testTarget}
        />
      )}
      {showTriggerForm && (
        <TriggerDialog
          onClose={() => setShowTriggerForm(false)}
          onSaved={async () => {
            setShowTriggerForm(false);
            flash("Trigger row created.");
            await loadData();
          }}
        />
      )}
    </div>
  );
}

function TemplateCell({
  template,
  busy,
  onToggle,
  onEdit,
  onTest,
  onProviderAction,
}: {
  template: NotificationTemplate;
  busy: boolean;
  onToggle: () => void;
  onEdit: () => void;
  onTest: () => void;
  onProviderAction: () => void;
}) {
  return (
    <div className={`template-cell ${template.is_enabled ? "" : "disabled"}`}>
      <div className="cell-topline">
        <span
          className={`status-pill ${template.is_enabled ? "ready" : "muted"}`}
        >
          {template.is_enabled ? "Enabled" : "Off"}
        </span>
        <button
          aria-label={`Turn ${template.channel_label} ${
            template.is_enabled ? "off" : "on"
          }`}
          className={`switch ${template.is_enabled ? "on" : ""}`}
          disabled={busy}
          onClick={onToggle}
          type="button"
        >
          <span />
        </button>
      </div>
      <strong className="template-name">
        {template.subject ||
          template.title ||
          template.provider_template_name ||
          "Message template"}
      </strong>
      <p>{template.body}</p>
      {template.channel === "whatsapp" && (
        <span
          className={`provider-status ${statusTone(template.provider_status)}`}
        >
          {template.provider_status_label}
        </span>
      )}
      <div className="cell-actions">
        <button onClick={onEdit} type="button">
          Edit
        </button>
        <button onClick={onTest} type="button">
          Test
        </button>
        {template.channel === "whatsapp" && (
          <button disabled={busy} onClick={onProviderAction} type="button">
            {template.provider_status === "not_synced" ? "Sync" : "Refresh"}
          </button>
        )}
      </div>
    </div>
  );
}

function DeliveryActivity({
  deliveries,
  onRefresh,
}: {
  deliveries: Delivery[];
  onRefresh: () => void;
}) {
  return (
    <section className="activity-panel">
      <div className="matrix-toolbar">
        <div>
          <h2>Recent delivery activity</h2>
          <p>
            Provider results make test sends and trigger runs easy to verify.
          </p>
        </div>
        <button
          className="button button-ghost button-small"
          onClick={onRefresh}
          type="button"
        >
          Refresh activity
        </button>
      </div>
      {deliveries.length ? (
        <div className="activity-list">
          {deliveries.map((delivery) => (
            <article key={delivery.id}>
              <span className={`activity-channel ${delivery.channel}`}>
                {delivery.channel === "whatsapp"
                  ? "WA"
                  : delivery.channel === "email"
                    ? "@"
                    : "P"}
              </span>
              <div className="activity-copy">
                <strong>
                  {delivery.trigger_name} · {delivery.channel_label}
                </strong>
                <span>
                  {delivery.recipient ||
                    delivery.error_message ||
                    "No recipient"}
                </span>
              </div>
              <span
                className={`status-pill ${statusTone(delivery.status)}`}
              >
                {delivery.status_label}
              </span>
              <time>{new Date(delivery.created_at).toLocaleString()}</time>
            </article>
          ))}
        </div>
      ) : (
        <div className="empty-activity">
          <span>↗</span>
          <strong>No delivery attempts yet</strong>
          <p>Use Test in any template cell or fire Login/Logout.</p>
        </div>
      )}
    </section>
  );
}

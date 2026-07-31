"use client";

import { FormEvent, ReactNode, useState } from "react";

import { api } from "@/lib/api";
import type {
  Channel,
  Delivery,
  NotificationTemplate,
  Trigger,
} from "@/lib/types";

export type EditorTarget = {
  trigger: Trigger;
  channel: Channel;
  template?: NotificationTemplate;
};

const channelLabels: Record<Channel, string> = {
  whatsapp: "WhatsApp",
  email: "Email",
  web_push: "Web Push",
};

function Modal({
  children,
  title,
  eyebrow,
  onClose,
  wide = false,
}: {
  children: ReactNode;
  title: string;
  eyebrow: string;
  onClose: () => void;
  wide?: boolean;
}) {
  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section
        aria-modal="true"
        className={`modal ${wide ? "modal-wide" : ""}`}
        onMouseDown={(event) => event.stopPropagation()}
        role="dialog"
      >
        <div className="modal-heading">
          <div>
            <div className="eyebrow">{eyebrow}</div>
            <h2>{title}</h2>
          </div>
          <button
            aria-label="Close dialog"
            className="icon-button"
            onClick={onClose}
            type="button"
          >
            ×
          </button>
        </div>
        {children}
      </section>
    </div>
  );
}

export function TemplateEditor({
  target,
  onClose,
  onSaved,
}: {
  target: EditorTarget;
  onClose: () => void;
  onSaved: () => void;
}) {
  const template = target.template;
  const [subject, setSubject] = useState(template?.subject ?? "");
  const [title, setTitle] = useState(template?.title ?? "");
  const [body, setBody] = useState(template?.body ?? "");
  const [providerName, setProviderName] = useState(
    template?.provider_template_name ??
      `${target.trigger.key.replaceAll(".", "_")}_${target.channel}`,
  );
  const [language, setLanguage] = useState(
    template?.provider_language ?? "en_US",
  );
  const [mapping, setMapping] = useState(
    JSON.stringify(
      template?.variable_mapping ?? { user_name: "user.first_name" },
      null,
      2,
    ),
  );
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      const payload = {
        trigger: target.trigger.id,
        channel: target.channel,
        subject,
        title,
        body,
        is_enabled: template?.is_enabled ?? true,
        variable_mapping: JSON.parse(mapping),
        provider_template_name:
          target.channel === "whatsapp" ? providerName : "",
        provider_language: language,
      };
      await api(
        template ? `/admin/templates/${template.id}/` : "/admin/templates/",
        {
          method: template ? "PATCH" : "POST",
          body: JSON.stringify(payload),
        },
      );
      onSaved();
    } catch (saveError) {
      setError(
        saveError instanceof SyntaxError
          ? "Variable mapping must be valid JSON."
          : saveError instanceof Error
            ? saveError.message
            : "Unable to save the template.",
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal
      eyebrow={`${target.trigger.name} · ${channelLabels[target.channel]}`}
      onClose={onClose}
      title={template ? "Edit template" : "Create template"}
      wide
    >
      <form className="modal-form" onSubmit={submit}>
        <div className="editor-grid">
          <div className="editor-fields">
            {target.channel === "email" && (
              <label className="field">
                <span>Email subject</span>
                <input
                  onChange={(event) => setSubject(event.target.value)}
                  required
                  value={subject}
                />
              </label>
            )}
            {target.channel === "web_push" && (
              <label className="field">
                <span>Notification title</span>
                <input
                  onChange={(event) => setTitle(event.target.value)}
                  required
                  value={title}
                />
              </label>
            )}
            {target.channel === "whatsapp" && (
              <div className="two-fields">
                <label className="field">
                  <span>Meta template name</span>
                  <input
                    onChange={(event) => setProviderName(event.target.value)}
                    pattern="[a-z0-9_]+"
                    required
                    value={providerName}
                  />
                </label>
                <label className="field">
                  <span>Language</span>
                  <input
                    onChange={(event) => setLanguage(event.target.value)}
                    required
                    value={language}
                  />
                </label>
              </div>
            )}
            <label className="field">
              <span>Message body</span>
              <textarea
                onChange={(event) => setBody(event.target.value)}
                placeholder="Hi {{user_name}}, your message goes here."
                required
                rows={6}
                value={body}
              />
              <small>
                Use double braces for variables, for example {"{{user_name}}"}.
              </small>
            </label>
            <label className="field">
              <span>Variable mapping</span>
              <textarea
                className="code-input"
                onChange={(event) => setMapping(event.target.value)}
                rows={5}
                value={mapping}
              />
              <small>Map each variable to a trigger context path.</small>
            </label>
          </div>
          <aside className="editor-preview">
            <div className="eyebrow">Live preview</div>
            <div className={`message-preview ${target.channel}`}>
              <div className="preview-provider">
                <span>
                  {target.channel === "whatsapp"
                    ? "WA"
                    : target.channel === "email"
                      ? "@"
                      : "P"}
                </span>
                <strong>{channelLabels[target.channel]}</strong>
              </div>
              {(subject || title) && <h3>{subject || title}</h3>}
              <p>{body || "Your message preview will appear here."}</p>
              <small>Variables resolve when the trigger fires.</small>
            </div>
          </aside>
        </div>
        {error && <div className="form-alert error">{error}</div>}
        <div className="modal-actions">
          <button
            className="button button-ghost"
            onClick={onClose}
            type="button"
          >
            Cancel
          </button>
          <button
            className="button button-primary"
            disabled={saving}
            type="submit"
          >
            {saving ? "Saving…" : "Save template"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

export function TestSendDialog({
  template,
  onClose,
  onSent,
}: {
  template: NotificationTemplate;
  onClose: () => void;
  onSent: (message: string) => void;
}) {
  const [destination, setDestination] = useState("");
  const [variables, setVariables] = useState(
    '{\n  "user_name": "Asif"\n}',
  );
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSending(true);
    setError("");
    try {
      const result = await api<Delivery[]>(
        `/admin/templates/${template.id}/test-send/`,
        {
          method: "POST",
          body: JSON.stringify({
            destination: destination || undefined,
            variables: JSON.parse(variables),
          }),
        },
      );
      const sent = result.filter((item) => item.status === "sent").length;
      const failed = result.length - sent;
      onSent(
        failed
          ? `Test finished: ${sent} sent, ${failed} skipped or failed.`
          : "Test notification sent successfully.",
      );
    } catch (sendError) {
      setError(
        sendError instanceof SyntaxError
          ? "Variables must be valid JSON."
          : sendError instanceof Error
            ? sendError.message
            : "Unable to send the test.",
      );
    } finally {
      setSending(false);
    }
  }

  return (
    <Modal
      eyebrow={template.channel_label}
      onClose={onClose}
      title="Send a test"
    >
      <form className="modal-form" onSubmit={submit}>
        <div className="test-summary">
          <span className={`activity-channel ${template.channel}`}>
            {template.channel === "whatsapp"
              ? "WA"
              : template.channel === "email"
                ? "@"
                : "P"}
          </span>
          <div>
            <strong>
              {template.subject ||
                template.title ||
                template.provider_template_name}
            </strong>
            <p>{template.body}</p>
          </div>
        </div>
        <label className="field">
          <span>
            Test destination <em>optional</em>
          </span>
          <input
            onChange={(event) => setDestination(event.target.value)}
            placeholder={
              template.channel === "whatsapp"
                ? "919876543210"
                : template.channel === "email"
                  ? "you@example.com"
                  : "OneSignal subscription ID"
            }
            value={destination}
          />
          <small>Leave blank to use your saved admin destination.</small>
        </label>
        <label className="field">
          <span>Test variables</span>
          <textarea
            className="code-input"
            onChange={(event) => setVariables(event.target.value)}
            rows={4}
            value={variables}
          />
        </label>
        {error && <div className="form-alert error">{error}</div>}
        <div className="modal-actions">
          <button
            className="button button-ghost"
            onClick={onClose}
            type="button"
          >
            Cancel
          </button>
          <button
            className="button button-primary"
            disabled={sending}
            type="submit"
          >
            {sending ? "Sending…" : "Send test"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

export function TriggerDialog({
  onClose,
  onSaved,
}: {
  onClose: () => void;
  onSaved: () => void;
}) {
  const [name, setName] = useState("");
  const [key, setKey] = useState("");
  const [description, setDescription] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      await api("/admin/triggers/", {
        method: "POST",
        body: JSON.stringify({ name, key, description, is_active: true }),
      });
      onSaved();
    } catch (saveError) {
      setError(
        saveError instanceof Error
          ? saveError.message
          : "Unable to create trigger.",
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal
      eyebrow="New event definition"
      onClose={onClose}
      title="Add a trigger"
    >
      <form className="modal-form" onSubmit={submit}>
        <label className="field">
          <span>Trigger name</span>
          <input
            autoFocus
            onChange={(event) => {
              const nextName = event.target.value;
              setName(nextName);
              setKey(
                nextName
                  .toLowerCase()
                  .trim()
                  .replace(/[^a-z0-9]+/g, ".")
                  .replace(/^\.+|\.+$/g, ""),
              );
            }}
            placeholder="Password reset"
            required
            value={name}
          />
        </label>
        <label className="field">
          <span>Event key</span>
          <input
            onChange={(event) => setKey(event.target.value)}
            pattern="[a-z0-9]+([._-][a-z0-9]+)*"
            placeholder="user.password_reset"
            required
            value={key}
          />
          <small>Website code uses this stable key to fire the trigger.</small>
        </label>
        <label className="field">
          <span>Description</span>
          <textarea
            onChange={(event) => setDescription(event.target.value)}
            placeholder="When does this trigger fire?"
            rows={3}
            value={description}
          />
        </label>
        {error && <div className="form-alert error">{error}</div>}
        <div className="modal-actions">
          <button
            className="button button-ghost"
            onClick={onClose}
            type="button"
          >
            Cancel
          </button>
          <button
            className="button button-primary"
            disabled={saving}
            type="submit"
          >
            {saving ? "Creating…" : "Create trigger row"}
          </button>
        </div>
      </form>
    </Modal>
  );
}

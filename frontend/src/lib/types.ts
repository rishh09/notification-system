export type Channel = "whatsapp" | "email" | "web_push";

export interface NotificationProfile {
  notification_email: string;
  whatsapp_phone: string;
  updated_at: string;
}

export interface User {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  is_staff: boolean;
  notification_profile: NotificationProfile;
}

export interface NotificationTemplate {
  id: number;
  trigger: number;
  channel: Channel;
  channel_label: string;
  subject: string;
  title: string;
  body: string;
  is_enabled: boolean;
  variable_mapping: Record<string, string>;
  provider_template_name: string;
  provider_language: string;
  provider_status: string;
  provider_status_label: string;
  provider_template_id: string;
  provider_error: string;
  created_at: string;
  updated_at: string;
}

export interface Trigger {
  id: number;
  key: string;
  name: string;
  description: string;
  is_active: boolean;
  templates: NotificationTemplate[];
  created_at: string;
  updated_at: string;
}

export interface Delivery {
  id: number;
  trigger: number;
  trigger_name: string;
  template: number | null;
  user: number | null;
  channel: Channel;
  channel_label: string;
  recipient: string;
  status: "pending" | "sent" | "failed" | "skipped";
  status_label: string;
  provider_message_id: string;
  provider_response: Record<string, unknown>;
  error_message: string;
  rendered_content: {
    subject?: string;
    title?: string;
    body?: string;
    variables?: Record<string, string>;
  };
  created_at: string;
}

export interface PushSubscription {
  id: number;
  subscription_id: string;
  device_label: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

# SignalDesk Notification System

SignalDesk is the full-stack notification system described in the backend assignment. It gives users a small website where Login and Logout events occur and gives administrators one Notification Settings matrix for WhatsApp, Email, and browser Web Push.

## Live application

- Frontend: https://notification-system-steel.vercel.app
- Backend health check: https://notification-system-api.vercel.app/api/health/
- Source code: https://github.com/rishh09/notification-system

## Current status

The assignment is implemented and deployed with live provider integrations:

- Django API, database models, authentication, and admin endpoints
- Database-driven Login and Logout triggers
- Twilio WhatsApp Sandbox, Postmark Email, and OneSignal Web Push
- Generic variable-aware notification dispatcher
- Next.js user dashboard and notification profile
- OneSignal browser subscription flow
- Admin trigger/template matrix
- Template create, edit, toggle, test-send, WhatsApp sync, and status actions
- Delivery activity records
- 16 passing backend tests and passing frontend lint
- Next.js frontend and Django backend deployed on Vercel
- Production PostgreSQL database hosted by Neon

The final production verification successfully sent the Login notification through WhatsApp, Email, and Web Push. Provider credentials are stored only in deployment environment variables and are not committed to this repository.

## Architecture

```text
User action (Login/Logout)
        |
        v
Django event trigger
        |
        v
Active database templates
        |
        +----> Twilio WhatsApp
        +----> Postmark Email
        +----> OneSignal Web Push
        |
        v
Notification delivery audit
```

The Next.js frontend calls the Django REST API using token authentication. Django stores application data and delivery history in Neon PostgreSQL. Each provider is attempted independently, so one failed channel does not prevent the remaining channels from running.

## Main data models

- **Trigger** — a stable application event such as `user.login` or `user.logout`.
- **NotificationTemplate** — channel-specific content, variable mappings, and enabled state for a trigger.
- **UserNotificationProfile** — the user's notification email and WhatsApp number.
- **PushSubscription** — the user's active OneSignal browser subscription.
- **NotificationDelivery** — the recipient, provider result, status, error, and timestamp for every attempt.

## Repository layout

```text
assignment/
├── backend/       Django + Django REST Framework
├── frontend/      Next.js + TypeScript
├── plan.md        Assignment scope and checkpoint tracker
└── README.md
```

## Local setup

### 1. Backend

From `backend/`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

The API runs at `http://localhost:8000`.

Health check:

```text
GET http://localhost:8000/api/health/
```

### 2. Frontend

From `frontend/`:

```bash
pnpm install
cp .env.example .env.local
pnpm dev
```

The website runs at `http://localhost:3000`.

## Demo accounts

After running `python manage.py seed_demo`:

| Role | Username | Default local password |
| --- | --- | --- |
| Administrator | `admin` | `AdminPass123!` |
| Member | `demo` | `UserPass123!` |

Change the defaults through `DEMO_ADMIN_PASSWORD` and `DEMO_USER_PASSWORD`. Never use the documented defaults for a public deployment.

The administrator opens `/admin/notifications`. The member opens `/dashboard`.

## Implemented triggers

### Login

Fires after successful Django authentication:

```text
user.login
```

### Logout

Fires before the user's API token is invalidated:

```text
user.logout
```

Both trigger records have separate WhatsApp, Email, and Web Push templates. The central dispatcher accepts any registered event key, so additional website events can be connected later.

## Notification behavior

When a trigger fires:

1. The backend loads the active trigger.
2. It loads enabled channel templates.
3. It resolves mappings such as `user_name -> user.first_name`.
4. It renders placeholders such as `{{user_name}}`.
5. It determines the user's channel destinations.
6. It attempts each enabled provider independently.
7. It records sent, failed, or skipped delivery results.

A provider failure does not prevent the other channels from being attempted.

## Environment variables

### Backend application

```env
DJANGO_SECRET_KEY=
DJANGO_DEBUG=false
TIME_ZONE=Asia/Kolkata
ALLOWED_HOSTS=
CORS_ALLOWED_ORIGINS=
CSRF_TRUSTED_ORIGINS=
FRONTEND_URL=
DATABASE_URL=
NOTIFICATION_PROVIDER_MODE=mock
```

Use `NOTIFICATION_PROVIDER_MODE=mock` while developing without provider credentials. Use `live` only after the sandbox accounts are configured.

### WhatsApp Cloud API

```env
WHATSAPP_PROVIDER=meta
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_BUSINESS_ACCOUNT_ID=
WHATSAPP_GRAPH_API_VERSION=v23.0
```

`WHATSAPP_PHONE_NUMBER_ID` is also compatible with the assignment's `PHONE_NUMBER_ID` variable name.

The business account ID is required for admin-side WhatsApp template creation and approval-status checks, even though the PDF lists only the access token and phone-number ID.

### Postmark

```env
POSTMARKAPP_TOKEN=
POSTMARK_FROM_EMAIL=
```

The sender address must be verified in the Postmark developer server.

### OneSignal backend

```env
ONESIGNAL_APP_ID=
ONESIGNAL_REST_API_KEY=
```

### Frontend

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api
NEXT_PUBLIC_ONESIGNAL_APP_ID=
```

Create separate OneSignal website configurations for localhost and the deployed Vercel origin.

## Provider setup

### WhatsApp

1. Create a Meta developer app.
2. Add the WhatsApp product.
3. Copy the sandbox/test phone-number ID and temporary token.
4. Add the receiving phone as an allowed test recipient.
5. Copy the WhatsApp Business Account ID for template management.
6. Add all values to the backend environment.
7. Save a WhatsApp template in Notification Settings.
8. Select **Sync**, wait for approval, then select **Refresh** and **Test**.

Temporary Meta tokens expire frequently.

### Twilio WhatsApp Sandbox

The deployed demo uses Twilio's WhatsApp Sandbox because Meta developer access
was unavailable during implementation:

```env
NOTIFICATION_PROVIDER_MODE=live
WHATSAPP_PROVIDER=twilio
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_WHATSAPP_FROM=whatsapp:+17372508034
TWILIO_WHATSAPP_CONTENT_SID=
```

The destination profile must use an international number such as
`919876543210`, and that number must first join the Twilio sandbox. Joining opens
a temporary customer-service window in which the local login/logout message
bodies can be delivered. New Twilio trial accounts may require the
account-specific `TWILIO_WHATSAPP_CONTENT_SID` displayed by the **Try out
WhatsApp** API panel. In that mode Twilio sends its fixed trial template while
SignalDesk retains the rendered login/logout content in the delivery audit.
Twilio Sandbox does not support this application's custom Meta template
synchronization actions. Those actions remain available when the application is
configured with `WHATSAPP_PROVIDER=meta`. The current production demonstration
uses Twilio's fixed sandbox content template.

### Postmark

1. Create a developer server.
2. Verify a sender signature.
3. Copy the server API token.
4. Configure `POSTMARKAPP_TOKEN` and `POSTMARK_FROM_EMAIL`.
5. Add an allowed email destination to the user's notification profile.

### OneSignal

1. Create a website application with Web Push enabled.
2. Configure the exact localhost or Vercel origin.
3. Add the App ID to both frontend and backend environments.
4. Add the App API key to the backend environment.
5. Use **Enable browser notifications** from the member dashboard.

The browser must grant notification permission before a real subscription ID can be stored.

## Admin API summary

```text
GET/POST       /api/admin/triggers/
GET/PATCH      /api/admin/triggers/{id}/
GET/POST       /api/admin/templates/
GET/PATCH      /api/admin/templates/{id}/
POST           /api/admin/templates/{id}/toggle/
POST           /api/admin/templates/{id}/test-send/
POST           /api/admin/templates/{id}/whatsapp-sync/
GET            /api/admin/templates/{id}/whatsapp-status/
GET            /api/admin/deliveries/
```

User endpoints:

```text
POST           /api/auth/login/
POST           /api/auth/logout/
GET            /api/auth/me/
PATCH          /api/auth/profile/
GET/POST       /api/push/subscriptions/
```

Admin endpoints require an authenticated staff user.

## Tests

Backend:

```bash
cd backend
.venv/bin/python manage.py test
```

Frontend:

```bash
cd frontend
pnpm lint
pnpm build
```

Provider API calls are mocked in automated tests so tests cannot send real messages.
The current suite contains 16 passing backend tests, and the frontend lint check
passes.

## Assignment demonstration

Before the demonstration, save the member's WhatsApp number and email address
and enable browser notifications from **My notifications**.

### Task A

1. Sign in as admin.
2. Configure all three Login templates.
3. Test WhatsApp, Email, and Web Push.
4. Sign in as the member using **Sign in and fire trigger**.
5. Verify the WhatsApp, Email, and Web Push delivery records.

### Task B

1. Configure all three Logout templates with different content.
2. Sign out as the member to fire Logout.
3. Verify three delivery records.

### Task C

1. Edit a template and test the updated content.
2. Disable one channel.
3. Fire the trigger and confirm that channel is absent.
4. Re-enable it and test again.

### Task D

- A trigger is a website event or condition that asks the notification engine to run.
- Examples include Login, Password Reset, and Order Placed.
- The supported channels are WhatsApp, Email, and browser Web Push.
- Templates are managed centrally so administrators do not need to work in three provider dashboards.
- Web Push is a browser notification delivered to a subscribed browser.

## Deployment

The production system consists of two Vercel projects connected to one Neon
PostgreSQL database:

- `notification-system-steel.vercel.app` — Next.js frontend
- `notification-system-api.vercel.app` — Django REST API
- Neon — managed PostgreSQL persistence

### Backend on Vercel

Import the repository as a Vercel project, choose `backend` as its root, and
configure the Django, Neon, CORS, provider, and demo-account environment
variables. `backend/vercel.json` runs migrations, seeds the configured demo
records, and collects static assets during the build.

Important production variables include:

```env
DATABASE_URL=
DJANGO_SECRET_KEY=
ALLOWED_HOSTS=
CORS_ALLOWED_ORIGINS=https://notification-system-steel.vercel.app
CSRF_TRUSTED_ORIGINS=https://notification-system-steel.vercel.app
FRONTEND_URL=https://notification-system-steel.vercel.app
NOTIFICATION_PROVIDER_MODE=live
```

Provider secrets must be configured in the Vercel environment settings and must
never be committed. Override both documented local demo passwords before making
a production deployment public.

### Frontend on Vercel

Import the repository as a second Vercel project, choose `frontend` as its root,
and set:

```env
NEXT_PUBLIC_API_URL=https://notification-system-api.vercel.app/api
NEXT_PUBLIC_ONESIGNAL_APP_ID=
```

The exact frontend origin must also be configured as the OneSignal Web Push site
URL. Users must allow browser notifications and subscribe from the dashboard
before Web Push can be delivered.

## Production verification

The final end-to-end Login run was accepted by all configured providers:

| Channel | Provider | Result |
| --- | --- | --- |
| WhatsApp | Twilio Sandbox | Sent |
| Email | Postmark | Sent |
| Web Push | OneSignal | Sent |

Delivery results are also available in the administrator's recent activity list.
Earlier failed diagnostic attempts can remain in this audit history; the latest
provider status identifies the result of the final run.

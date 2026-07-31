# Notification System Assignment Plan

This file is the implementation checklist and scope reference for the assignment.

## 1. Confirmed assignment scope

- [x] Build a Python + Django backend.
- [ ] Deploy the backend on Render.
- [x] Build a frontend using React/Next.js or equivalent.
- [ ] Deploy the frontend on Vercel.
- [x] Provide a user-facing website where notification-producing events occur.
- [x] Provide a custom admin Notification Settings screen.
- [x] Implement WhatsApp Cloud API integration; live sandbox verification remains.
- [x] Implement Postmark integration and verify real inbox delivery.
- [x] Implement OneSignal browser Web Push; live sandbox verification remains.
- [x] Store triggers, channel templates, enabled/disabled state, and variable mappings.
- [x] Fully implement Login and Logout in mock-provider mode.
- [x] Manage templates from the custom admin panel.
- [ ] Submit repository URL, live backend URL, live frontend URL, and README.

## 2. Selected MVP scope

### Fully wired triggers

- [x] Login
- [x] Logout

The notification engine must remain generic so additional event-based triggers can be connected later.

### Supported channels for every trigger

- [x] WhatsApp adapter and template workflow
- [x] Email adapter
- [x] Browser Web Push adapter and subscription workflow

### Explicitly out of scope for the MVP

- Mobile app push
- Production WhatsApp credentials
- Scheduled inactivity triggers
- Celery/Redis
- E-commerce/order functionality
- Multi-tenant organizations
- Advanced analytics

## 3. Planned repository structure

```text
assignment/
├── backend/
├── frontend/
├── plan.md
├── README.md
└── .gitignore
```

## 4. Backend plan

Recommended stack:

- Django
- Django REST Framework
- PostgreSQL in production
- Simple local database for development
- Environment-based configuration

### Backend foundation

- [x] Create Django project.
- [x] Add REST API configuration.
- [x] Configure authentication.
- [x] Add admin authorization.
- [x] Configure CORS for the frontend.
- [x] Add environment configuration.
- [x] Add `.env.example`.
- [x] Ensure real `.env` files are ignored.
- [x] Add Render production configuration.

### Data models

- [x] `Trigger`
  - Name
  - Unique event key
  - Description
  - Active status
- [x] `NotificationTemplate`
  - Trigger
  - Channel
  - Email subject
  - Push title
  - Message body
  - Enabled status
  - Variable mappings
  - Provider template name/status where required
  - Unique trigger/channel constraint
- [x] `UserNotificationProfile`
  - User
  - Email destination
  - WhatsApp test phone number
- [x] `PushSubscription`
  - User
  - OneSignal subscription ID
  - Active status
- [x] `NotificationDelivery`
  - Trigger
  - Channel
  - Recipient
  - Success/failure
  - Provider response/error
  - Timestamp

`NotificationDelivery` is not explicitly required by the PDF, but it will make testing and debugging reliable.

### Trigger and template APIs

- [x] List triggers.
- [x] Create a trigger.
- [x] Edit a trigger.
- [x] Delete/deactivate a trigger.
- [x] List templates by trigger.
- [x] Create a template.
- [x] Edit a template.
- [x] Enable/disable a template.
- [x] Test-send a template.

### Notification engine

- [x] Implement a generic `dispatch_notification(trigger_key, user, context)` service.
- [x] Load templates for the selected trigger.
- [x] Skip missing or disabled channel templates.
- [x] Resolve template variables from the supplied context.
- [x] Attempt every enabled channel independently.
- [x] Prevent one provider failure from blocking the other channels.
- [x] Record provider results.

### Provider adapters

- [x] WhatsApp Cloud API adapter.
- [x] WhatsApp template synchronization/status handling.
- [x] Postmark email adapter.
- [x] OneSignal Web Push adapter.
- [x] Consistent provider error handling.
- [x] Safe logging without exposing tokens.

### Authentication event wiring

- [x] Fire Login after successful authentication.
- [x] Fire Logout before the user session/token is invalidated.
- [x] Seed Login and Logout trigger records.

## 5. Frontend plan

Recommended stack:

- Next.js
- TypeScript
- Responsive accessible UI

### User-facing experience

- [x] Login page.
- [x] Authenticated dashboard.
- [x] Logout action.
- [x] Browser Web Push subscription action.
- [x] Display notification subscription state.
- [x] Store/update required user notification destinations.

### Admin experience

- [x] Protect admin routes.
- [x] Build Notification Settings table.
- [x] Render one row per trigger.
- [x] Render WhatsApp, Email, and Web Push columns.
- [x] Add Trigger flow.
- [x] Create template modal/form.
- [x] Edit template modal/form.
- [x] Channel enabled/disabled toggle.
- [x] Test-send action.
- [x] WhatsApp synchronization/status action.
- [x] Loading, success, and error feedback.
- [x] Responsive layout for smaller screens.

## 6. Admin table acceptance criteria

Each trigger/channel cell must expose:

- [x] Template exists/missing state.
- [x] Create or Edit action.
- [x] Enabled/disabled state.
- [x] Test-send action.
- [x] Provider state when applicable.

Expected starting table:

| Trigger | WhatsApp | Email | Web Push |
| --- | --- | --- | --- |
| Login | Template controls | Template controls | Template controls |
| Logout | Template controls | Template controls | Template controls |

## 7. Sandbox account setup

### WhatsApp

- [ ] Create Meta developer app.
- [ ] Add WhatsApp product.
- [ ] Obtain test phone number.
- [ ] Obtain temporary access token.
- [ ] Add test recipient phone number.
- [ ] Configure required backend environment variables.
- [ ] Create/synchronize templates.
- [ ] Confirm templates can be used for test sends.
- [x] Activate a temporary Twilio WhatsApp Sandbox while Meta appeal is pending.
- [x] Add a switchable Twilio delivery adapter without replacing Meta.
- [x] Configure the rotated Twilio token locally and confirm phone delivery.
- [x] Record a real Twilio provider message ID.
- [x] Accept Twilio's pre-approved Sandbox template as the temporary WhatsApp demo flow.
- [x] Confirm the account-specific default Twilio template is received on WhatsApp.
- [ ] Verify the intended Login/Logout copy on WhatsApp.
- [x] Confirm the Twilio Sandbox cannot create or use custom Login/Logout templates.
- [ ] Register a production WhatsApp sender before creating the required custom templates.

### Postmark

- [x] Create developer server.
- [x] Verify sender email.
- [x] Obtain server API token.
- [x] Configure the backend with Postmark's official `POSTMARK_API_TEST` token.
- [x] Confirm the email payload is accepted by Postmark in non-delivery test mode.
- [x] Replace the test token with a real server API token.
- [x] Confirm delivery to a real inbox.

### OneSignal

- [x] Create website application.
- [x] Enable Web Push only for the localhost app.
- [x] Configure the frontend SDK and public App ID.
- [x] Subscribe a browser with Chrome notification permission granted.
- [x] Save and validate the active browser subscription ID.
- [x] Configure backend environment variables and verify the App API key.
- [x] Confirm OneSignal reports one successful Chrome Web Push delivery.
- [x] Identify macOS application notifications being disabled for Google Chrome.
- [x] Enable Google Chrome notifications in macOS and confirm a visible notification.

## 8. Environment configuration

PDF-listed provider variables:

```env
WHATSAPP_ACCESS_TOKEN=
PHONE_NUMBER_ID=
POSTMARKAPP_TOKEN=
POSTMARK_FROM_EMAIL=
ONESIGNAL_APP_ID=
ONESIGNAL_REST_API_KEY=
```

Expected application variables:

```env
DJANGO_SECRET_KEY=
DJANGO_DEBUG=
DATABASE_URL=
ALLOWED_HOSTS=
CORS_ALLOWED_ORIGINS=
FRONTEND_URL=
BACKEND_URL=
```

Additional Meta or OneSignal configuration will be documented if required by the selected API workflow.

## 9. Testing checkpoints

### Automated checks

- [x] Model constraints and template validation tests.
- [x] Trigger CRUD API tests.
- [x] Template CRUD API tests.
- [x] Toggle API tests.
- [x] Variable substitution tests.
- [x] Provider adapters mocked in automated tests.
- [x] Login trigger dispatch test.
- [x] Logout trigger dispatch test.
- [x] Frontend production build succeeds.
- [x] Backend tests pass.

### Assignment demonstration checks

- [ ] Task A: Login sends WhatsApp.
- [ ] Task A: Login sends Email.
- [ ] Task A: Login sends Web Push.
- [ ] Task B: Logout sends different WhatsApp content.
- [ ] Task B: Logout sends different Email content.
- [ ] Task B: Logout sends different Web Push content.
- [ ] Task C: Edit a template and receive the updated message.
- [ ] Task C: Disable one channel and confirm it does not send.
- [ ] Task C: Re-enable the channel and confirm it sends.
- [ ] Task D: Explain triggers, channels, admin-managed templates, and Web Push.

## 10. Deployment checkpoints

### Render

- [ ] Create backend service.
- [ ] Configure PostgreSQL.
- [ ] Configure environment variables.
- [ ] Run migrations.
- [ ] Create admin user.
- [ ] Confirm health/API endpoint.
- [ ] Confirm production provider integrations.

### Vercel

- [ ] Configure frontend project.
- [ ] Configure backend URL.
- [ ] Configure OneSignal frontend values.
- [ ] Confirm HTTPS browser push subscription.
- [ ] Confirm admin and user flows against the live backend.

## 11. Documentation and submission

- [x] Root README.
- [x] Local backend setup instructions.
- [x] Local frontend setup instructions.
- [x] Admin login/creation instructions.
- [x] Test user instructions.
- [x] Implemented trigger list.
- [x] Environment variable reference.
- [x] Sandbox provider setup.
- [ ] Render deployment URL.
- [ ] Vercel deployment URL.
- [ ] Repository URL.
- [x] Demonstration steps for Tasks A-C.
- [x] Short answers/preparation for Task D.

## 12. Implementation sequence

### Checkpoint 1 - Foundation

- [x] Repository initialized.
- [x] Backend and frontend scaffolded.
- [x] Environment and ignore files added.
- [x] Both projects pass their initial framework checks/build.

### Checkpoint 2 - Backend domain

- [x] Models and migrations complete.
- [x] Seed data complete.
- [x] Trigger/template admin APIs complete.
- [x] Backend tests pass.

### Checkpoint 3 - Notification providers

- [x] Provider adapters complete.
- [x] Temporary Twilio WhatsApp Sandbox adapter complete.
- [x] Generic dispatch complete.
- [x] Test-send complete.
- [x] Provider calls covered by mocked tests.

### Checkpoint 4 - Frontend product

- [x] User login/logout flow complete.
- [x] Browser subscription flow complete.
- [x] Admin table complete.
- [x] Template create/edit/toggle/test flows complete.

### Checkpoint 5 - End-to-end verification

- [x] Login trigger works on all channels in mock-provider mode.
- [x] Live Login trigger accepted by Twilio WhatsApp Sandbox, Postmark, and OneSignal in one dispatch.
- [x] Logout trigger works on all channels in mock-provider mode; live sandbox remains.
- [x] Edit and toggle behavior verified locally.
- [x] Error and skipped-delivery states verified locally.

### Checkpoint 6 - Deployment and handoff

- [ ] Render deployment complete.
- [ ] Vercel deployment complete.
- [ ] Live end-to-end verification complete.
- [x] README complete.
- [ ] Submission checklist complete.

## 13. Definition of done

The assignment is complete only when:

1. Login and Logout are real website events.
2. Each event sends through all three enabled channels.
3. The admin can create, edit, test, and toggle templates from the custom table.
4. Browser Web Push subscription works.
5. Both deployments are live.
6. The README and submission links are complete.

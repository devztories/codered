# CODERED INVENTIONS notification system

## Website notifications

- Customer and admin notification records are stored in the existing `notifications_notification` table.
- The notification bell appears in the public navigation and the admin/employee workspace.
- The browser polls the notification feed every 8 seconds for near-real-time updates.
- Users can open a notification, which marks it read and navigates to the related order/admin page.
- "Mark all read" updates the current user's notifications only.
- Notification feed and read endpoints require authentication and are scoped to the signed-in user.

## Events covered

### Customer
- New order/project request received.
- Order/project status changes.
- Certificate request status changes.
- Payment proof received and payment status changes.
- Customer-visible employee progress updates.
- Admin messages attached to an order (OrderUpdate).

### Admin
- New customer registration.
- New project/order request or ready-made order.
- New payment proof submission.
- New website contact enquiry.
- New customer review.
- New customer chatbot message (including guest messages).

Admin notifications are sent to active staff/superuser accounts. Configure operational WhatsApp numbers separately as described below.

## Database migration

A customer WhatsApp opt-in field was added to `UserProfile`.

Run:

```bash
python manage.py migrate
python manage.py check
```

No existing notification table migration is required; the existing notifications app table is reused.

## WhatsApp Cloud API configuration

The integration uses Meta's WhatsApp Cloud API. Copy `.env.example` values into the deployment environment and set:

- `WHATSAPP_ACCESS_TOKEN`: Meta Cloud API access token.
- `WHATSAPP_PHONE_NUMBER_ID`: WhatsApp Business phone-number ID from Meta.
- `WHATSAPP_ADMIN_NUMBERS`: comma-separated admin destination numbers in international format.
- `WHATSAPP_CUSTOMER_NOTIFICATIONS_ENABLED=true`: master switch for customer WhatsApp delivery.
- `WHATSAPP_TEMPLATE_NAME`: approved Meta message template name.
- `WHATSAPP_TEMPLATE_LANGUAGE`: template language code, normally `en`.
- `SITE_BASE_URL`: canonical public website URL.

The template must be approved in WhatsApp Manager and have three body parameters in this order:
1. Notification title.
2. Notification message.
3. Website link or the fallback text.

When a template name is configured, the integration sends template messages suitable for business-initiated notifications. Without a template name, it attempts a regular text message; Meta generally permits free-form text only within the 24-hour customer service window.

### Customer consent

Customers must explicitly opt in using **Profile → Receive project updates on WhatsApp**. Customer WhatsApp delivery is disabled unless both that per-customer checkbox and `WHATSAPP_CUSTOMER_NOTIFICATIONS_ENABLED=true` are set. Do not enable the global switch until the business has obtained and retained the required WhatsApp opt-in.

Admin notifications can be delivered to `WHATSAPP_ADMIN_NUMBERS` and to staff account phone numbers. Admin WhatsApp numbers should be numbers that have consented to receive operational alerts.

## Deployment notes

- Add all WhatsApp environment variables to the hosting provider (Railway/Render/Vercel environment settings); do not commit real access tokens to Git.
- Apply migrations after deployment.
- The app uses short HTTP polling rather than Django Channels/WebSockets, so no Redis service or ASGI server change is required.
- If Meta rejects a message, the website notification is still saved and remains visible in the notification bell.

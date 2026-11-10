# CodeRed Inventions ΓÇô Notifications Setup

## What is included

- In-app notifications for signed-in customers and staff administrators.
- The website polls the notification feed every 8 seconds; this is near-real-time polling, not WebSockets.
- Customer alerts: request received, order created, order status/stage changes, certificate status changes, payment submitted/verified/rejected, visible project progress, and support replies.
- Admin alerts: customer registration, project requests, new orders, payment proofs, contact enquiries, reviews, customer chatbot messages, and customer order messages.
- Optional WhatsApp Cloud API delivery for administrators and opted-in customers.

## Database update

Run this after deploying the updated project:

```bash
python manage.py migrate
```

This creates the `UserProfile.whatsapp_notifications_enabled` opt-in field. The existing `notifications.Notification` model and its initial migration are retained.

## WhatsApp environment variables

Configure these as secret environment variables in Railway (or your deployment provider):

```env
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_API_VERSION=v23.0
WHATSAPP_ADMIN_NUMBERS=91XXXXXXXXXX
WHATSAPP_ADMIN_NOTIFICATIONS_ENABLED=true
WHATSAPP_CUSTOMER_NOTIFICATIONS_ENABLED=false
WHATSAPP_TEMPLATE_NAME=codered_notification
WHATSAPP_TEMPLATE_LANGUAGE=en
SITE_BASE_URL=https://coderedinvention.vercel.app
```

- `WHATSAPP_ACCESS_TOKEN`: Meta WhatsApp Cloud API access token.
- `WHATSAPP_PHONE_NUMBER_ID`: the API Phone Number ID shown in the WhatsApp API setup page; it is not the visible phone number.
- `WHATSAPP_ADMIN_NUMBERS`: comma-separated administrator recipient numbers in international format, digits only (for example `919876543210`).
- `WHATSAPP_ADMIN_NOTIFICATIONS_ENABLED`: enables/disables admin WhatsApp alerts.
- `WHATSAPP_CUSTOMER_NOTIFICATIONS_ENABLED`: global customer WhatsApp switch. It defaults off.
- `WHATSAPP_TEMPLATE_NAME`: the exact approved WhatsApp message-template name.
- `WHATSAPP_TEMPLATE_LANGUAGE`: the approved template language code.
- `SITE_BASE_URL`: public website base URL used to make notification links absolute.

## WhatsApp template requirements

Create and get approval for a WhatsApp template whose BODY contains exactly three text parameters, in this order:

1. Notification title (`{{1}}`)
2. Notification message (`{{2}}`)
3. Website link (`{{3}}`)

For example, the body can be:

```text
{{1}}
{{2}}
Open: {{3}}
```

The template name and language configured in environment variables must match the approved template. Meta may require template approval before business-initiated messages can be sent.

## Customer opt-in

A customer can enable WhatsApp notifications from the account profile form. The customer must have a valid phone number on their account and must explicitly opt in. Customer WhatsApp notifications also require `WHATSAPP_CUSTOMER_NOTIFICATIONS_ENABLED=true`.

## Important security notes

- Never put a real access token in source code, `.env.example`, GitHub, or a chat message.
- Store production credentials only in the deployment provider's secret/environment-variable settings.
- Use Meta's test number and a verified test recipient first. Switch to the registered business number after the production WhatsApp Business Account setup is complete.
- WhatsApp delivery errors are logged and do not interrupt the website action that generated the notification.

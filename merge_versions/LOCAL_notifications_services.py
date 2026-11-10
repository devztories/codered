import json
import logging
import os
import re
import urllib.error
import urllib.request

from django.conf import settings
from django.db import transaction

from .models import Notification

logger = logging.getLogger(__name__)


def _normalise_phone(value):
    """Return a WhatsApp Cloud API recipient number in international digits."""
    return re.sub(r"[^0-9]", "", str(value or ""))


def send_whatsapp(phone, text):
    """Send a WhatsApp Cloud API text message; safely no-op when not configured."""
    token = os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
    api_version = os.getenv("WHATSAPP_API_VERSION", "v22.0").strip()
    recipient = _normalise_phone(phone)

    if not token or not phone_number_id or not recipient:
        return False

    template_name = os.getenv("WHATSAPP_TEMPLATE_NAME", "").strip()
    if template_name:
        parts = str(text).split("\n")
        title = parts[1] if len(parts) > 1 else "Notification"
        body_text = parts[2] if len(parts) > 2 else str(text)
        link = parts[3] if len(parts) > 3 else ""
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": os.getenv("WHATSAPP_TEMPLATE_LANGUAGE", "en").strip()
                },
                "components": [{
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": title[:200]},
                        {"type": "text", "text": body_text[:900]},
                        {"type": "text", "text": link[:200] or "Open your CODERED account"},
                    ],
                }],
            },
        }
    else:
        # Text messages are normally accepted only while the 24-hour customer
        # service window is open. Configure an approved template for proactive alerts.
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": str(text)[:3500]},
        }
    url = f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            return 200 <= response.status < 300
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        logger.warning("WhatsApp notification failed: %s", exc)
        return False


def _whatsapp_for_user(user, title, message, url):
    body = f"CODERED INVENTIONS\n{title}\n{message}"
    if url:
        site_url = os.getenv("SITE_BASE_URL", "").rstrip("/")
        if site_url:
            body += f"\n{site_url}{url}"

    if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
        account_phone = _normalise_phone(getattr(user, "phone_number", ""))
        if account_phone:
            send_whatsapp(account_phone, body)
        return

    if os.getenv("WHATSAPP_CUSTOMER_NOTIFICATIONS_ENABLED", "false").lower() != "true":
        return

    try:
        profile = user.profile
        opted_in = profile.whatsapp_notifications_enabled
    except Exception:
        opted_in = False

    if opted_in:
        send_whatsapp(getattr(user, "phone_number", ""), body)


def create_notification(user, title, message, url="", send_whatsapp_message=True):
    if not user or not getattr(user, "is_active", True):
        return None

    notification = Notification.objects.create(
        user=user,
        title=str(title)[:160],
        message=str(message),
        url=str(url)[:300],
    )
    transaction.on_commit(
        lambda: __import__("notifications.push", fromlist=["send_web_push"]).send_web_push(
            user, notification.title, notification.message, notification.url
        )
    )
    # Send externally only after the DB transaction has committed.
    if send_whatsapp_message:
        transaction.on_commit(
            lambda: _whatsapp_for_user(user, notification.title, notification.message, notification.url)
        )
    return notification


def notify_admins(title, message, url="/admin/"):
    from accounts.models import User

    admins = User.objects.filter(is_active=True).filter(
        models_q_staff()
    ).distinct()
    recipients = list(admins.iterator())
    notifications = [
        create_notification(admin, title, message, url, send_whatsapp_message=False)
        for admin in recipients
    ]
    numbers = set(
        _normalise_phone(value)
        for value in os.getenv("WHATSAPP_ADMIN_NUMBERS", "").split(",")
        if _normalise_phone(value)
    )
    numbers.update(
        _normalise_phone(getattr(admin, "phone_number", ""))
        for admin in recipients
        if _normalise_phone(getattr(admin, "phone_number", ""))
    )
    body = f"CODERED INVENTIONS\n{title}\n{message}"
    site_url = os.getenv("SITE_BASE_URL", "").rstrip("/")
    if site_url and url:
        body += f"\n{site_url}{url}"
    if numbers:
        transaction.on_commit(lambda: [send_whatsapp(number, body) for number in numbers])
    return notifications


def models_q_staff():
    from django.db.models import Q
    return Q(is_staff=True) | Q(is_superuser=True)


def notify_customer(user, title, message, url=""):
    return create_notification(user, title, message, url)

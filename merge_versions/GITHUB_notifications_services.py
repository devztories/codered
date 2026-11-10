"""In-app and optional WhatsApp notification helpers for CodeRed Inventions."""
import json
import logging
import os
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.db import transaction

from .models import Notification

logger = logging.getLogger(__name__)


def _site_url(path):
    base = os.getenv("SITE_BASE_URL", "").strip().rstrip("/")
    if path.startswith("http://") or path.startswith("https://"):
        return path
    return f"{base}{path}" if base else path


def _phone(value):
    return re.sub(r"\D", "", str(value or ""))


def _admin_recipients():
    numbers = {
        _phone(item)
        for item in os.getenv("WHATSAPP_ADMIN_NUMBERS", "").split(",")
        if _phone(item)
    }
    # Also include staff phone numbers, if present.
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        numbers.update(
            _phone(value)
            for value in User.objects.filter(
                is_active=True, is_staff=True
            ).exclude(phone_number__isnull=True).exclude(phone_number="")
            .values_list("phone_number", flat=True)
            if _phone(value)
        )
    except Exception:
        logger.exception("Unable to load administrator WhatsApp numbers")
    return sorted(numbers)


def _send_whatsapp(phone, title, message, url):
    """Send an approved WhatsApp template; failures never interrupt site actions."""
    token = os.getenv("WHATSAPP_ACCESS_TOKEN", "").strip()
    phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "").strip()
    template_name = os.getenv("WHATSAPP_TEMPLATE_NAME", "").strip()
    language = os.getenv("WHATSAPP_TEMPLATE_LANGUAGE", "en").strip() or "en"
    if not (token and phone_number_id and template_name and phone):
        return False

    version = os.getenv("WHATSAPP_API_VERSION", "v23.0").strip()
    endpoint = f"https://graph.facebook.com/{version}/{phone_number_id}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": phone,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language},
            "components": [{
                "type": "body",
                "parameters": [
                    {"type": "text", "text": str(title)[:1024]},
                    {"type": "text", "text": str(message)[:1024]},
                    {"type": "text", "text": _site_url(url)[:1024] or "Open CodeRed Inventions"},
                ],
            }],
        },
    }
    request = Request(
        endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=8) as response:
            return 200 <= response.status < 300
    except (HTTPError, URLError, TimeoutError, OSError):
        logger.exception("WhatsApp notification delivery failed")
        return False
    except Exception:
        logger.exception("Unexpected WhatsApp notification error")
        return False


def notify_user(user, title, message, url="/dashboard/", whatsapp=True):
    if not user or not getattr(user, "is_active", True):
        return None
    notification = Notification.objects.create(
        user=user, title=str(title)[:160], message=str(message), url=url or "/dashboard/"
    )
    if whatsapp and os.getenv("WHATSAPP_CUSTOMER_NOTIFICATIONS_ENABLED", "false").lower() == "true":
        try:
            profile = user.profile
            opted_in = bool(profile.whatsapp_notifications_enabled)
        except Exception:
            opted_in = False
        phone = _phone(getattr(user, "phone_number", ""))
        if opted_in and phone:
            transaction.on_commit(
                lambda: _send_whatsapp(phone, title, message, url)
            )
    return notification


def notify_admins(title, message, url="/admin/"):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    admins = User.objects.filter(is_active=True, is_staff=True)
    for user in admins.iterator():
        notify_user(user, title, message, url, whatsapp=False)

    if os.getenv("WHATSAPP_ADMIN_NOTIFICATIONS_ENABLED", "true").lower() == "true":
        for phone in _admin_recipients():
            transaction.on_commit(
                lambda p=phone: _send_whatsapp(p, title, message, url)
            )

import json, logging, os
from django.conf import settings
from .models import PushSubscription
logger = logging.getLogger(__name__)

def send_web_push(user, title, message, url="/", notification_id=None):
    public = os.getenv("VAPID_PUBLIC_KEY", "").strip()
    private = os.getenv("VAPID_PRIVATE_KEY", "").strip()
    subject = os.getenv("VAPID_SUBJECT", "mailto:admin@coderedinvention.vercel.app").strip()
    if not (public and private):
        return
    try:
        from pywebpush import webpush, WebPushException
    except ImportError:
        logger.warning("pywebpush is not installed; browser push skipped")
        return
    payload = json.dumps({"id": notification_id, "title": str(title)[:100], "body": str(message)[:240], "url": url or "/"})
    for sub in PushSubscription.objects.filter(user=user).iterator():
        try:
            webpush(subscription_info={"endpoint": sub.endpoint, "keys": {"p256dh": sub.p256dh, "auth": sub.auth}}, data=payload, vapid_private_key=private, vapid_claims={"sub": subject})
        except Exception as exc:
            status = getattr(getattr(exc, "response", None), "status_code", None)
            if status in (404, 410):
                sub.delete()
            else:
                logger.warning("Web push delivery failed: %s", exc)

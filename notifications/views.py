from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET, require_POST

from .models import Notification


@login_required
@require_GET
def feed(request):
    qs = Notification.objects.filter(user=request.user).order_by("-created_at")
    unread_count = qs.filter(is_read=False).count()
    items = [
        {
            "id": item.pk,
            "title": item.title,
            "message": item.message,
            "url": item.url,
            "created_at": item.created_at.isoformat(),
            "is_read": item.is_read,
        }
        for item in qs[:15]
    ]
    return JsonResponse({"unread_count": unread_count, "items": items})


@login_required
@require_POST
def mark_read(request, pk):
    item = get_object_or_404(Notification, pk=pk, user=request.user)
    if not item.is_read:
        item.is_read = True
        item.save(update_fields=["is_read"])
    return JsonResponse({"ok": True})


@login_required
@require_POST
def mark_all_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({"ok": True})


@login_required
@require_POST
def subscribe_push(request):
    import json
    from django.conf import settings
    from .models import PushSubscription
    try:
        data = json.loads(request.body.decode("utf-8"))
        sub = data.get("subscription", data)
        keys = sub.get("keys", {})
        endpoint = sub["endpoint"]
        p256dh, auth = keys["p256dh"], keys["auth"]
        if not endpoint.startswith("https://") or not p256dh or not auth:
            raise ValueError("Invalid subscription")
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return JsonResponse({"ok": False, "error": "Invalid subscription data"}, status=400)
    PushSubscription.objects.update_or_create(endpoint=endpoint, defaults={"user": request.user, "p256dh": p256dh, "auth": auth, "user_agent": request.META.get("HTTP_USER_AGENT", "")[:500]})
    return JsonResponse({"ok": True})

@login_required
@require_POST
def unsubscribe_push(request):
    import json
    from .models import PushSubscription
    try:
        data = json.loads(request.body.decode("utf-8"))
        endpoint = data.get("endpoint", "")
    except (ValueError, TypeError):
        endpoint = ""
    if endpoint:
        PushSubscription.objects.filter(user=request.user, endpoint=endpoint).delete()
    return JsonResponse({"ok": True})

SERVICE_WORKER_JS = """\
self.addEventListener('install', function () { self.skipWaiting(); });
self.addEventListener('activate', function (event) { event.waitUntil(self.clients.claim()); });

self.addEventListener('push', function (event) {
  var data = {};
  try { data = event.data ? event.data.json() : {}; } catch (e) { data = {}; }
  var title = data.title || 'CODERED INVENTIONS';
  var options = {
    body: data.body || 'You have a new update.',
    icon: '/static/images/icon-192.png',
    badge: '/static/images/badge-96.png',
    data: { url: data.url || '/' },
    timestamp: Date.now(),
    vibrate: [120, 60, 120]
  };
  // A unique tag per notification keeps several updates visible instead of replacing each other.
  if (data.id) options.tag = 'codered-' + data.id;
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', function (event) {
  event.notification.close();
  var target = new URL('/', self.location.origin);
  try {
    var requested = new URL((event.notification.data && event.notification.data.url) || '/', self.location.origin);
    if (requested.origin === self.location.origin) target = requested;
  } catch (e) {}
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function (windows) {
      for (var i = 0; i < windows.length; i++) {
        var client = windows[i];
        if (client.url.indexOf(self.location.origin) === 0 && 'focus' in client) {
          return client.focus().then(function (focused) {
            if (focused && 'navigate' in focused) return focused.navigate(target.href);
          });
        }
      }
      return self.clients.openWindow(target.href);
    })
  );
});
"""


def service_worker(request):
    from django.http import HttpResponse
    response = HttpResponse(SERVICE_WORKER_JS, content_type="application/javascript")
    response["Service-Worker-Allowed"] = "/"
    response["Cache-Control"] = "no-cache"
    return response

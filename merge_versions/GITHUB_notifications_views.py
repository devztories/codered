import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from .models import Notification


@login_required
def notification_feed(request):
    items = Notification.objects.filter(user=request.user).order_by("-created_at")[:20]
    return JsonResponse({
        "unread_count": Notification.objects.filter(user=request.user, is_read=False).count(),
        "notifications": [
            {
                "id": item.pk,
                "title": item.title,
                "message": item.message,
                "url": item.url,
                "is_read": item.is_read,
                "created_at": item.created_at.isoformat(),
            }
            for item in items
        ],
    })


@login_required
@require_POST
def mark_notification_read(request, pk):
    item = get_object_or_404(Notification, pk=pk, user=request.user)
    if not item.is_read:
        item.is_read = True
        item.save(update_fields=["is_read"])
    return JsonResponse({"ok": True})


@login_required
@require_POST
def mark_all_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({"ok": True})

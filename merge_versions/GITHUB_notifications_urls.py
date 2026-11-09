from django.urls import path

from . import views

app_name = "notifications"

urlpatterns = [
    path("feed/", views.notification_feed, name="feed"),
    path("<int:pk>/read/", views.mark_notification_read, name="read"),
    path("read-all/", views.mark_all_notifications_read, name="read_all"),
]

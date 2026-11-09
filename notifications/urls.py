from django.urls import path
from . import views

app_name = "notifications"
urlpatterns = [
    path("feed/", views.feed, name="feed"),
    path("push/subscribe/", views.subscribe_push, name="push_subscribe"),
    path("push/unsubscribe/", views.unsubscribe_push, name="push_unsubscribe"),
    path("sw.js", views.service_worker, name="service_worker"),
    path("<int:pk>/read/", views.mark_read, name="mark_read"),
    path("read-all/", views.mark_all_read, name="mark_all_read"),
]

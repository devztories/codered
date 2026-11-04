from django.urls import path
from . import views

app_name = "payments"
urlpatterns = [path("<str:order_id>/", views.pay, name="pay")]

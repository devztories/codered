from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from orders.models import Order
from payments.models import Payment
from certificates.models import Certificate
from notifications.models import Notification

@login_required
def home(request):
    orders = Order.objects.filter(user=request.user).select_related("project", "request", "request__category").prefetch_related("payments", "updates").order_by("-created_at")
    payments = Payment.objects.filter(user=request.user).select_related("order", "order__project").order_by("-created_at")
    certificates = Certificate.objects.filter(user=request.user).select_related("order").order_by("-created_at")
    return render(request, "dashboard/home.html", {
        "orders": orders,
        "payments": payments,
        "certificates": certificates,
        "notifications": Notification.objects.filter(user=request.user).order_by("-created_at")[:8],
    })

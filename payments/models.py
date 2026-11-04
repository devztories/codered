from django.conf import settings
from django.db import models
from django.utils import timezone

from orders.models import Order


class Payment(models.Model):
    STATUS = [
        ("pending", "Pending"),
        ("submitted", "Submitted"),
        ("verified", "Verified"),
        ("failed", "Rejected"),
        ("refunded", "Refunded"),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=[("upi", "UPI QR")], default="upi")
    status = models.CharField(max_length=20, choices=STATUS, default="pending")
    receipt = models.ImageField(upload_to="payment-receipts/", blank=True)
    transaction_id = models.CharField(max_length=120, blank=True)
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_payments",
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.status == "verified" and not self.verified_at:
            self.verified_at = timezone.now()
        super().save(*args, **kwargs)
        if self.status == "verified" and self.order.status != "paid":
            self.order.status = "paid"
            self.order.save(update_fields=["status", "updated_at"])

    def __str__(self):
        return f"{self.order.order_id} - {self.status}"


class PaymentSettings(models.Model):
    upi_id = models.CharField(max_length=120, blank=True)
    upi_name = models.CharField(max_length=120, blank=True)
    bank_details = models.TextField(blank=True)
    qr_code = models.ImageField(upload_to="payment-settings/", blank=True)
    instructions = models.TextField(blank=True)

    def __str__(self):
        return "UPI payment settings"

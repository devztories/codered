from django.contrib import admin, messages
from django.utils import timezone

from .models import Payment, PaymentSettings


@admin.action(description="Verify selected UPI payments with submitted proof")
def verify_payments(modeladmin, request, queryset):
    verified = 0
    skipped = 0
    for payment in queryset.select_related("order"):
        if payment.status != "submitted" or not payment.receipt or not payment.transaction_id:
            skipped += 1
            continue
        payment.status = "verified"
        payment.verified_by = request.user
        payment.verified_at = timezone.now()
        payment.save()
        verified += 1
    if verified:
        modeladmin.message_user(request, f"{verified} payment(s) verified.", messages.SUCCESS)
    if skipped:
        modeladmin.message_user(request, f"{skipped} payment(s) skipped: proof or transaction ID missing, or not submitted.", messages.WARNING)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("order", "user", "amount", "method", "status", "transaction_id", "verified_by", "verified_at", "created_at")
    list_filter = ("status", "method", "created_at")
    search_fields = ("order__order_id", "user__email", "transaction_id")
    readonly_fields = ("created_at", "verified_by", "verified_at")
    actions = [verify_payments]


@admin.register(PaymentSettings)
class PaymentSettingsAdmin(admin.ModelAdmin):
    list_display = ("upi_id", "upi_name")

    def has_add_permission(self, request):
        return not PaymentSettings.objects.exists() and super().has_add_permission(request)
    fieldsets = (
        ("UPI payment details", {"fields": ("upi_id", "upi_name", "qr_code", "instructions", "bank_details")}),
    )

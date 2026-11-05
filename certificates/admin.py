from django.contrib import admin
from .models import Certificate, CertificateDesignSettings


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("certificate_id", "recipient_name", "project_name", "completion_date", "revoked")
    list_filter = ("revoked", "completion_date")
    search_fields = ("certificate_id", "recipient_name", "project_name", "user__email")
    readonly_fields = ("certificate_id", "created_at",)
    fields = ("order", "user", "recipient_name", "project_name", "completion_date", "certificate_id", "revoked", "created_at")


@admin.register(CertificateDesignSettings)
class CertificateDesignSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ("Main certificate text", {"fields": ("certificate_heading", "ribbon_text", "intro_text", "completion_text", "body_text")}),
        ("Certificate identifiers", {"fields": ("certificate_prefix", "company_id", "issue_date_label", "verification_label")}),
        ("Mentor and company details", {"fields": ("mentor_signature_text", "mentor_signature_image", "mentor_title", "company_name", "website", "location")}),
    )

    def has_add_permission(self, request):
        return not CertificateDesignSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

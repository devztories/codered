from django.contrib import admin
from .models import ContactMessage, SocialLink, SiteSettings

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ("company_name", "contact_email", "phone", "whatsapp_number", "updated_at")
    fieldsets = (("Branding", {"fields": ("company_name", "tagline", "logo", "about_text")}),
                 ("Talk to our team", {"fields": ("contact_email", "phone", "whatsapp_number")}))

admin.site.register(ContactMessage)
admin.site.register(SocialLink)

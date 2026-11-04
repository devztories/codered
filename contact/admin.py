from django.contrib import admin
from .models import ContactMessage, SocialLink, SiteSettings
admin.site.register(ContactMessage)
admin.site.register(SocialLink)
admin.site.register(SiteSettings)

from django.contrib import admin
from .models import Category, SubCategory, Project, ProjectImage

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "project_type", "is_ready_made", "price", "is_published", "customization_available")
    list_filter = ("project_type", "is_ready_made", "is_published", "customization_available")
    search_fields = ("name", "short_description", "technologies")
    prepopulated_fields = {"slug": ("name",)}

admin.site.register(Category)
admin.site.register(SubCategory)
admin.site.register(ProjectImage)

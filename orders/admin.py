from django.contrib import admin
from .models import ProjectRequest, Order, Quotation, OrderUpdate

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'title', 'user', 'order_type', 'stage', 'status', 'amount', 'updated_at')
    list_filter = ('order_type', 'stage', 'status', 'created_at')
    search_fields = ('order_id', 'title', 'user__email')
    list_editable = ('stage', 'status')
    readonly_fields = ('order_id', 'created_at', 'updated_at')

@admin.register(ProjectRequest)
class ProjectRequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'request_type', 'project', 'user', 'budget', 'deadline', 'created_at')
    list_filter = ('request_type', 'created_at')
    search_fields = ('title', 'user__email', 'required_features')
admin.site.register(Quotation)
admin.site.register(OrderUpdate)

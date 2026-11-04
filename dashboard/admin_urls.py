from django.urls import path
from . import admin_views
app_name = 'control'
urlpatterns = [
    path('', admin_views.admin_home, name='home'),
    path('<slug:module>/', admin_views.admin_module, name='module'),
    path('orders/<int:pk>/details/', admin_views.admin_order_detail, name='order_detail'),
    path('<slug:module>/add/', admin_views.admin_edit, name='add'),
    path('<slug:module>/<int:pk>/edit/', admin_views.admin_edit, name='edit'),
    path('<slug:module>/<int:pk>/delete/', admin_views.admin_delete, name='delete'),
]

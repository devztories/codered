from django.urls import path
from . import views
app_name = 'orders'
urlpatterns = [
    path('new/', views.request_project, name='request'),
    path('buy/<slug:slug>/', views.buy_project, name='buy'),
    path('<str:order_id>/certificate-request/', views.request_certificate, name='certificate_request'),
    path('<str:order_id>/', views.order_detail, name='detail'),
]

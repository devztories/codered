from django.urls import path
from .views import home
from .employee_views import employee_home, employee_order
app_name='dashboard'
urlpatterns=[path('',home,name='home'),path('employee/',employee_home,name='employee_home'),path('employee/orders/<str:order_id>/',employee_order,name='employee_order')]

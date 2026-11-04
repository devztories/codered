from django.urls import path
from . import views
app_name='reviews'
urlpatterns=[path('',views.list_reviews,name='list'),path('new/<str:order_id>/',views.create,name='create')]

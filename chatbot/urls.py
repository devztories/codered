from django.urls import path
from .views import message
app_name='chatbot'
urlpatterns=[path('message/',message,name='message')]

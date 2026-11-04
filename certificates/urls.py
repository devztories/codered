from django.urls import path
from . import views
app_name='certificates'
urlpatterns=[path('',views.index,name='index'),path('generate/<str:order_id>/',views.generate,name='generate'),path('download/<str:certificate_id>/',views.download,name='download'),path('preview/<str:certificate_id>/',views.preview,name='preview'),path('verify/<str:certificate_id>/',views.verify,name='verify')]

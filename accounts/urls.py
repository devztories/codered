from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
app_name='accounts'
urlpatterns=[path('register/',views.register,name='register'),path('login/',views.login_view,name='login'),path('logout/',views.logout_view,name='logout'),path('profile/',views.profile,name='profile'),path('password-reset/',auth_views.PasswordResetView.as_view(template_name='accounts/form.html',email_template_name='accounts/password_reset_email.html'),name='password_reset'),path('password-reset/done/',auth_views.PasswordResetDoneView.as_view(),name='password_reset_done'),path('reset/<uidb64>/<token>/',auth_views.PasswordResetConfirmView.as_view(template_name='accounts/form.html'),name='password_reset_confirm'),path('reset/done/',auth_views.PasswordResetCompleteView.as_view(),name='password_reset_complete')]

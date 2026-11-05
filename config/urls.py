from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static
from core_views import home,about,contact_page,faq,payment_info,service_unavailable
urlpatterns=[path('',home,name='home'),path('errors/503/',service_unavailable,name='service_unavailable'),path('about/',about,name='about'),path('contact/',contact_page,name='contact'),path('faq/',faq,name='faq'),path('payment-information/',payment_info,name='payment_info'),path('accounts/',include('accounts.urls')),path('catalog/',include('catalog.urls')),path('services/',include('services.urls')),path('orders/',include('orders.urls')),path('payments/',include('payments.urls')),path('certificates/',include('certificates.urls')),path('reviews/',include('reviews.urls')),path('chat/',include('chatbot.urls')),path('dashboard/',include('dashboard.urls'))]
if settings.DEBUG: urlpatterns+=static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
# The branded staff dashboard replaces Django's default admin interface.
urlpatterns += [path('admin/', include('dashboard.admin_urls'))]

# Django custom error handlers (active when DEBUG=False).
handler400 = 'core_views.bad_request'
handler403 = 'core_views.permission_denied'
handler404 = 'core_views.page_not_found'
handler500 = 'core_views.server_error'

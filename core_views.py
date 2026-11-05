from django.shortcuts import render

from catalog.models import Project
from reviews.models import Review
from services.models import Service


def home(request):
    return render(request, "public/home.html", {
        "services": Service.objects.filter(is_published=True).order_by("id"),
        # Show both published and unpublished projects in the portfolio.
        "projects": Project.objects.select_related("category").order_by("-created_at")[:6],
        "reviews": Review.objects.filter(is_approved=True)[:3],
    })


def about(request):
    return render(request, "public/about.html")


def contact_page(request):
    from contact.views import submit
    return submit(request)


def faq(request):
    return render(request, "public/faq.html")


def payment_info(request):
    from payments.models import PaymentSettings
    return render(request, "public/payment_info.html", {
        "payment_settings": PaymentSettings.objects.first()
    })


# Branded error pages used by Django's standard error handlers.
def bad_request(request, exception):
    return render(request, "errors/400.html", status=400)


def permission_denied(request, exception):
    return render(request, "errors/403.html", status=403)


def page_not_found(request, exception):
    return render(request, "errors/404.html", status=404)


def server_error(request):
    return render(request, "errors/500.html", status=500)


def service_unavailable(request):
    return render(request, "errors/503.html", status=503)

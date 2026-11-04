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

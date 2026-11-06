from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from catalog.models import Project
from .forms import ProjectRequestForm
from .models import Order


@login_required
def request_project(request):
    initial = {"request_type": request.GET.get("type", "business")}
    project_id = request.GET.get("project")
    if project_id and project_id.isdigit():
        selected_project = Project.objects.select_related("category").filter(pk=project_id).first()
        if selected_project:
            initial["project"] = selected_project.pk
            initial["title"] = selected_project.name
            initial["category"] = selected_project.category_id
            if selected_project.project_type == "academic" and selected_project.is_ready_made:
                initial["request_type"] = "ready_custom"
            else:
                initial["request_type"] = "academic_custom" if selected_project.project_type == "academic" else "business"
    form = ProjectRequestForm(request.POST or None, request.FILES or None, initial=initial if request.method == "GET" else None)
    if request.method == "POST" and form.is_valid():
        project_request = form.save(commit=False)
        project_request.user = request.user
        project_request.save()
        order_type = "academic_custom" if project_request.request_type in {"academic_custom", "ready_custom"} else "business"
        order = Order.objects.create(
            user=request.user, request=project_request, project=project_request.project, title=project_request.title,
            amount=0, order_type=order_type, status="under_review",
        )
        messages.success(request, "Your request was submitted. You can track it from your dashboard.")
        return redirect("orders:detail", order_id=order.order_id)
    project_options = [
        {"id": item.pk, "name": item.name, "category": item.category_id or ""}
        for item in Project.objects.select_related("category").order_by("name")
    ]
    return render(request, "orders/request.html", {
        "form": form,
        "request_type": initial.get("request_type", "business"),
        "project_options": project_options,
    })


@login_required
@require_POST
def buy_project(request, slug):
    project = get_object_or_404(Project, slug=slug, project_type="academic", is_ready_made=True, is_published=True)
    order = Order.objects.create(
        user=request.user, project=project, title=project.name, amount=project.price,
        order_type="academic", status="awaiting_payment",
    )
    messages.success(request, f'{project.name} added to your orders. Complete the UPI payment to confirm your purchase.')
    return redirect("payments:pay", order_id=order.order_id)


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    payment_verified = order.payments.filter(status="verified").exists()
    payment_submitted = order.payments.filter(status="submitted").exists()
    return render(request, "orders/detail.html", {
        "order": order,
        "work_updates": order.work_updates.filter(is_customer_visible=True).select_related("employee__user"),
        "payment_verified": payment_verified,
        "payment_submitted": payment_submitted,
        "is_complete": order.stage in {"completed", "delivered"},
        "payment_submitted_popup": request.GET.get("payment_review") == "1",
    })


@login_required
@require_POST
def request_certificate(request, order_id):
    """Store a lightweight request only; no certificate file is generated or uploaded."""
    from django.utils import timezone
    order = get_object_or_404(Order, order_id=order_id, user=request.user)
    payment_verified = order.payments.filter(status="verified").exists()
    if order.stage not in {"completed", "delivered"}:
        messages.warning(request, "Certificate requests are available after project completion.")
    elif not payment_verified:
        messages.warning(request, "Your payment must be verified before requesting a certificate.")
    elif order.certificate_request_status == "sent":
        messages.info(request, "Your certificate has already been marked as sent by our team.")
    elif order.certificate_request_status == "requested":
        messages.info(request, "Your certificate request is already with our admin team.")
    else:
        order.certificate_request_status = "requested"
        order.certificate_requested_at = timezone.now()
        order.save(update_fields=["certificate_request_status", "certificate_requested_at", "updated_at"])
        messages.success(request, "Certificate request submitted. Our team will send your certificate via WhatsApp.")
    return redirect("orders:detail", order_id=order.order_id)

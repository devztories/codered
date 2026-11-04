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
        selected_project = Project.objects.filter(pk=project_id, project_type="academic", is_ready_made=True).first()
        if selected_project:
            initial["project"] = selected_project.pk
            initial["title"] = selected_project.name
            initial["category"] = selected_project.category_id
            initial["request_type"] = "ready_custom"
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
        for item in Project.objects.filter(project_type="academic", is_ready_made=True).order_by("name")
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
        "payment_verified": payment_verified,
        "payment_submitted": payment_submitted,
        "is_complete": order.stage in {"completed", "delivered"},
        "payment_submitted_popup": request.GET.get("payment_review") == "1",
    })

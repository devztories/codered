from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from .models import Category, Project


def projects(request):
    qs = Project.objects.select_related("category", "subcategory")
    q = request.GET.get("q", "").strip()
    cat = request.GET.get("category", "").strip()
    project_type = request.GET.get("type", "").strip()
    sort = request.GET.get("sort", "newest")

    if q:
        qs = qs.filter(
            Q(name__icontains=q)
            | Q(short_description__icontains=q)
            | Q(technologies__icontains=q)
        )

    if cat:
        qs = qs.filter(category__slug=cat)

    if project_type in {"business", "academic"}:
        qs = qs.filter(project_type=project_type)

    qs = qs.order_by("price" if sort == "price" else "-created_at")

    # Each swipeable carousel slide contains up to 10 projects.
    project_list = list(qs)
    project_batches = [
        project_list[index:index + 10]
        for index in range(0, len(project_list), 10)
    ]

    return render(request, "catalog/projects.html", {
        "project_batches": project_batches,
        "project_count": len(project_list),
        "categories": Category.objects.filter(is_active=True),
        "q": q,
        "selected": cat,
        "project_type": project_type,
    })


def detail(request, slug):
    project = get_object_or_404(
        Project.objects.select_related("category", "subcategory"),
        slug=slug,
    )
    return render(request, "catalog/detail.html", {"project": project})

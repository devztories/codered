from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.core.paginator import Paginator
from .models import Category, Project

CARDS_PER_ROW = 10
ROWS_PER_PAGE = 10


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

    # One page = 10 rows, and each row is a swipeable strip of 10 project cards.
    paginator = Paginator(qs, ROWS_PER_PAGE * CARDS_PER_ROW)
    page_obj = paginator.get_page(request.GET.get("page"))
    items = list(page_obj.object_list)
    rows = [items[i:i + CARDS_PER_ROW] for i in range(0, len(items), CARDS_PER_ROW)]

    return render(request, "catalog/projects.html", {
        "page_obj": page_obj,
        "rows": rows,
        "project_count": paginator.count,
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

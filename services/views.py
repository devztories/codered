from django.shortcuts import render
from .models import Service
def index(request): return render(request,'services/index.html',{'services':Service.objects.filter(is_published=True)})

from django import forms
from django.contrib.auth.decorators import login_required
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib import messages
from orders.models import Order
from .models import Review
class ReviewForm(forms.ModelForm):
 class Meta: model=Review; fields=('rating','title','content','image')
@login_required
def create(request,order_id):
 order=get_object_or_404(Order,user=request.user,order_id=order_id,status__in=['completed','delivered'])
 form=ReviewForm(request.POST or None,request.FILES or None)
 if request.method=='POST' and form.is_valid(): r=form.save(commit=False); r.user=request.user; r.order=order; r.save(); messages.success(request,'Review submitted for approval.'); return redirect('dashboard:home')
 return render(request,'reviews/form.html',{'form':form})
def list_reviews(request): return render(request,'reviews/list.html',{'reviews':Review.objects.filter(is_approved=True).select_related('user')})

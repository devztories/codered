from django import forms
from django.contrib.auth.decorators import login_required
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib import messages
from orders.models import Order
from .models import Review
from certificates.models import Certificate
class ReviewForm(forms.ModelForm):
 class Meta: model=Review; fields=('rating','title','content','image')
@login_required
def create(request,order_id):
 order=get_object_or_404(Order,user=request.user,order_id=order_id)
 if not Certificate.objects.filter(order=order, user=request.user, revoked=False).exists():
  messages.info(request, 'Generate your project certificate before submitting a review.')
  return redirect('certificates:index')
 if Review.objects.filter(order=order).exists():
  messages.info(request, 'You have already submitted a review for this project.')
  return redirect('dashboard:home')
 form=ReviewForm(request.POST or None,request.FILES or None)
 if request.method=='POST' and form.is_valid(): r=form.save(commit=False); r.user=request.user; r.order=order; r.save(); messages.success(request,'Review submitted for approval.'); return redirect('dashboard:home')
 return render(request,'reviews/form.html',{'form':form})
def list_reviews(request): return render(request,'reviews/list.html',{'reviews':Review.objects.filter(is_approved=True).select_related('user')})

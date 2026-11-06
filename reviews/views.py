from django import forms
from django.contrib.auth.decorators import login_required
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib import messages
from orders.models import Order
from .models import Review
class ReviewForm(forms.ModelForm):
 class Meta: model=Review; fields=('rating','title','content')
@login_required
def create(request,order_id):
 order=get_object_or_404(Order,user=request.user,order_id=order_id)
 if order.certificate_request_status != 'sent':
  messages.info(request, 'Our team must mark your certificate request as sent before you can submit a review.')
  return redirect('orders:detail', order_id=order.order_id)
 if Review.objects.filter(order=order).exists():
  messages.info(request, 'You have already submitted a review for this project.')
  return redirect('dashboard:home')
 form=ReviewForm(request.POST or None)
 if request.method=='POST' and form.is_valid(): r=form.save(commit=False); r.user=request.user; r.order=order; r.save(); messages.success(request,'Review submitted for approval.'); return redirect('dashboard:home')
 return render(request,'reviews/form.html',{'form':form})
def list_reviews(request): return render(request,'reviews/list.html',{'reviews':Review.objects.filter(is_approved=True).select_related('user')})

from django.shortcuts import render,redirect
from django.contrib import messages
from .forms import ContactForm
def submit(request):
 form=ContactForm(request.POST or None)
 if request.method=='POST' and form.is_valid(): form.save(); messages.success(request,'Thanks! Your enquiry has been received.'); return redirect('home')
 return render(request,'contact/index.html',{'form':form})

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.db.models import Sum
from django.forms import modelform_factory
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST
from catalog.models import Project, Category, SubCategory
from orders.models import ProjectRequest, Order, Quotation, OrderUpdate
from payments.models import Payment, PaymentSettings
from accounts.models import User, UserProfile
from contact.models import ContactMessage
from reviews.models import Review
from certificates.models import Certificate
from services.models import Service
from chatbot.models import ChatConversation, ChatMessage
from notifications.models import Notification

MODULES = {
 'projects': {'title':'Projects','subtitle':'Business and academic project catalogue','model':Project,'icon':'◈','exclude':('slug','created_at')},
 'categories': {'title':'Categories','subtitle':'Create and organise catalogue categories','model':Category,'icon':'▤','exclude':('slug',)},
 'subcategories': {'title':'Subcategories','subtitle':'Organise projects under categories','model':SubCategory,'icon':'▧','exclude':('slug',)},
 'services': {'title':'Services','subtitle':'Manage services shown on the website','model':Service,'icon':'✧','exclude':('slug',)},
 'requests': {'title':'Project Requests','subtitle':'Business builds, academic builds and feature requests','model':ProjectRequest,'icon':'✉','exclude':('created_at',)},
 'orders': {'title':'Orders','subtitle':'Purchases and project delivery status','model':Order,'icon':'▣','exclude':('order_id','created_at','updated_at')},
 'payments': {'title':'Payments','subtitle':'Review UPI receipts and verify payments','model':Payment,'icon':'₹','exclude':('created_at','verified_at')},
 'payment-settings': {'title':'Payment Settings','subtitle':'UPI ID, display name and QR code','model':PaymentSettings,'icon':'◉','exclude':()},
 'users': {'title':'Users','subtitle':'Customer and administrator accounts','model':User,'icon':'♙','exclude':('password','last_login','groups','user_permissions','date_joined')},
 'messages': {'title':'Enquiries','subtitle':'Customer contact messages','model':ContactMessage,'icon':'☏','exclude':('created_at',)},
 'reviews': {'title':'Reviews','subtitle':'Moderate customer feedback','model':Review,'icon':'☆','exclude':('created_at',)},
 'certificates': {'title':'Certificates','subtitle':'Issue and manage project certificates','model':Certificate,'icon':'▧','exclude':()},
 'conversations': {'title':'Chatbot Conversations','subtitle':'Read customer conversations and support requests','model':ChatConversation,'icon':'✦','exclude':('session_key','created_at','updated_at')},
}

@staff_member_required(login_url='/accounts/login/')
def admin_home(request):
 context={'active':'overview','counts':[
 ('Total projects',Project.objects.count(),'projects','◈'),('Unpublished',Project.objects.filter(is_published=False).count(),'projects','◉'),('Project requests',ProjectRequest.objects.count(),'requests','✉'),('Orders',Order.objects.count(),'orders','▣'),('Pending payments',Payment.objects.filter(status__in=['pending','submitted']).count(),'payments','₹'),('Customers',User.objects.filter(is_staff=False).count(),'users','♙')],
 'recent_requests':ProjectRequest.objects.select_related('user','project').order_by('-created_at')[:6],
 'recent_orders':Order.objects.select_related('user','project').order_by('-created_at')[:6],
 'total_revenue':Payment.objects.filter(status='verified').aggregate(total=Sum('amount'))['total'] or 0}
 return render(request,'dashboard/admin_home.html',context)

@staff_member_required(login_url='/accounts/login/')
def admin_module(request,module):
 cfg=MODULES.get(module)
 if not cfg: raise Http404
 qs=cfg['model'].objects.all().order_by('-pk')[:250]
 rows=[]
 for obj in qs:
  title=str(obj)
  meta=''
  status='Active'
  value=''
  if module=='projects': meta=obj.get_project_type_display(); status='Published' if obj.is_published else 'Unpublished'; value=f'₹{obj.price}'
  elif module=='requests': meta=str(obj.user); status=obj.get_request_type_display(); value=f"Budget ₹{obj.budget}" if obj.budget else 'Budget not specified'
  elif module=='orders': meta=str(obj.user); status=obj.get_status_display(); value=f'₹{obj.amount}'
  elif module=='payments': meta=str(obj.user); status=obj.get_status_display(); value=f'₹{obj.amount}'
  elif module=='users': meta=obj.email or obj.phone_number or ''; status='Administrator' if obj.is_staff else 'Customer'
  elif module=='messages': meta=f'{obj.name} · {obj.email}'; status='Resolved' if obj.is_resolved else 'Open'
  elif module=='reviews': meta=str(obj.user); status='Approved' if obj.is_approved else 'Needs review'
  elif module=='certificates': meta=obj.project_name; status='Revoked' if obj.revoked else 'Active'
  elif module=='categories': meta=obj.slug; status='Active' if obj.is_active else 'Hidden'; value=f'{obj.projects.count()} projects'
  elif module=='conversations': meta=str(obj.user or 'Guest'); status='Human support' if obj.mode=='human' else 'AI assistant'; value=f'{obj.messages.count()} messages'
  order_pk = None
  if module == 'requests':
   try: order_pk = obj.order.pk
   except Exception: order_pk = None
  rows.append({'pk':obj.pk,'title':title,'meta':meta,'status':status,'value':value,'order_pk':order_pk})
 return render(request,'dashboard/admin_module.html',{'active':module,'module':cfg,'module_key':module,'rows':rows,'total':cfg['model'].objects.count(),'add_url':reverse('control:add',args=[module]),'can_add':module not in {'requests','orders','payments','messages','reviews','conversations'}})

@staff_member_required(login_url='/accounts/login/')
def admin_edit(request,module,pk=None):
 cfg=MODULES.get(module)
 if not cfg: raise Http404
 Model=cfg['model']; obj=get_object_or_404(Model,pk=pk) if pk else None
 exclude=list(cfg.get('exclude',()))
 if module=='users':
  exclude += ['is_superuser','is_staff']
 Form=modelform_factory(Model,exclude=tuple(exclude))
 form=Form(request.POST or None,request.FILES or None,instance=obj)
 if request.method=='POST' and form.is_valid():
  saved=form.save()
  if module=='users' and not obj and not saved.has_usable_password(): saved.set_unusable_password(); saved.save()
  messages.success(request,f'{cfg["title"][:-1] if cfg["title"].endswith("s") else cfg["title"]} saved successfully.')
  return redirect('control:module',module=module)
 return render(request,'dashboard/admin_form.html',{'active':module,'module':cfg,'module_key':module,'form':form,'editing':bool(obj),'object':obj})

@staff_member_required(login_url='/accounts/login/')
@require_POST
def admin_delete(request,module,pk):
 cfg=MODULES.get(module)
 if not cfg: raise Http404
 obj=get_object_or_404(cfg['model'],pk=pk); obj.delete(); messages.success(request,'Item deleted successfully.')
 return redirect('control:module',module=module)


def admin_entry(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('/accounts/login/?next=/admin/')
    return admin_home(request)


@staff_member_required(login_url='/accounts/login/')
def admin_order_detail(request, pk):
    order = get_object_or_404(Order.objects.select_related('user', 'project', 'request'), pk=pk)
    return render(request, 'dashboard/admin_order_detail.html', {
        'active': 'orders', 'order': order,
        'payments': order.payments.select_related('user', 'verified_by').order_by('-created_at'),
        'certificates': order.certificates.order_by('-created_at'),
        'updates': order.updates.select_related('created_by').order_by('-created_at'),
        'quotations': order.quotations.order_by('-created_at'),
    })

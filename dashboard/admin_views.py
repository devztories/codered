from functools import wraps
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from django.forms import modelform_factory, ModelForm
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST
from catalog.models import Project, Category, SubCategory
from orders.models import ProjectRequest, Order, Quotation, OrderUpdate, OrderAssignment, OrderWorkUpdate
from payments.models import Payment, PaymentSettings
from accounts.models import User, UserProfile, EmployeeProfile
from contact.models import ContactMessage, SiteSettings
from reviews.models import Review
from services.models import Service
from chatbot.models import ChatConversation, ChatMessage
from notifications.models import Notification


EMPLOYEE_BLOCKED_MODULES = {"payments", "payment-settings", "site-settings", "certificate-requests"}

def workspace_access_required(view):
    """Allow staff administrators and active employees into the shared workspace."""
    @login_required(login_url="/accounts/login/")
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if request.user.is_staff or request.user.is_superuser:
            request.is_employee_workspace = False
            return view(request, *args, **kwargs)
        profile = EmployeeProfile.objects.filter(
            user=request.user, is_active=True, user__is_active=True
        ).first()
        if not profile:
            messages.error(request, "You do not have permission to access this workspace.")
            return redirect("dashboard:home")
        request.is_employee_workspace = True
        request.employee_profile = profile
        return view(request, *args, **kwargs)
    return wrapped

def ensure_module_access(request, module):
    if getattr(request, "is_employee_workspace", False) and module in EMPLOYEE_BLOCKED_MODULES:
        raise Http404

MODULES = {
 'projects': {'title':'Projects','subtitle':'Business and academic project catalogue','model':Project,'icon':'◈','exclude':('slug','created_at')},
 'categories': {'title':'Categories','subtitle':'Create and organise catalogue categories','model':Category,'icon':'▤','exclude':('slug',)},
 'subcategories': {'title':'Subcategories','subtitle':'Organise projects under categories','model':SubCategory,'icon':'▧','exclude':('slug',)},
 'services': {'title':'Services','subtitle':'Manage services shown on the website','model':Service,'icon':'✧','exclude':('slug',)},
 'requests': {'title':'Project Requests','subtitle':'Business builds, academic builds and feature requests','model':ProjectRequest,'icon':'✉','exclude':('created_at',)},
 'orders': {'title':'Orders','subtitle':'Purchases and project delivery status','model':Order,'icon':'▣','exclude':('order_id','created_at','updated_at')},
 'payments': {'title':'Payments','subtitle':'Review UPI receipts and verify payments','model':Payment,'icon':'₹','exclude':('created_at','verified_at')},
 'payment-settings': {'title':'Payment Settings','subtitle':'UPI ID, display name and QR code','model':PaymentSettings,'icon':'◉','exclude':()},
 'employees': {'title':'Employees','subtitle':'Manage employee accounts and access','model':EmployeeProfile,'icon':'♟','exclude':('employee_code','created_at')},
 'users': {'title':'Users','subtitle':'Customer and administrator accounts','model':User,'icon':'♙','exclude':('password','last_login','groups','user_permissions','date_joined')},
 'site-settings': {'title':'Contact Settings','subtitle':'Manage WhatsApp, email and phone details shown on Contact Us','model':SiteSettings,'icon':'☎','exclude':('updated_at',)},
 'messages': {'title':'Enquiries','subtitle':'Customer contact messages','model':ContactMessage,'icon':'☏','exclude':('created_at',)},
 'reviews': {'title':'Reviews','subtitle':'Moderate customer feedback','model':Review,'icon':'☆','exclude':('created_at',)},
 'certificate-requests': {'title':'Certificate Requests','subtitle':'Customer requests awaiting manual WhatsApp delivery','model':Order,'icon':'✉','exclude':()},
 'conversations': {'title':'Chatbot Conversations','subtitle':'Read customer conversations and support requests','model':ChatConversation,'icon':'✦','exclude':('session_key','created_at','updated_at')},
}

@workspace_access_required
def admin_home(request):
 counts=[
 ('Total projects',Project.objects.count(),'projects','◈'),('Unpublished',Project.objects.filter(is_published=False).count(),'projects','◉'),('Project requests',ProjectRequest.objects.count(),'requests','✉'),('Orders',Order.objects.count(),'orders','▣'),('Customers',User.objects.filter(is_staff=False).count(),'users','♙'),('Employees',EmployeeProfile.objects.filter(is_active=True).count(),'employees','♟')]
 if not request.is_employee_workspace:
  counts.insert(4, ('Pending payments',Payment.objects.filter(status__in=['pending','submitted']).count(),'payments','₹'))
 context={'active':'overview','counts':counts,
 'recent_requests':ProjectRequest.objects.select_related('user','project').order_by('-created_at')[:6],
 'recent_orders':Order.objects.select_related('user','project').order_by('-created_at')[:6],
 'is_employee_workspace':request.is_employee_workspace,
 'total_revenue':Payment.objects.filter(status='verified').aggregate(total=Sum('amount'))['total'] or 0 if not request.is_employee_workspace else None}
 return render(request,'dashboard/admin_home.html',context)

@workspace_access_required
def admin_module(request,module):
 ensure_module_access(request, module)
 cfg=MODULES.get(module)
 if not cfg: raise Http404
 qs=cfg['model'].objects.all().order_by('-pk')[:250]
 if module == 'certificate-requests':
  qs=Order.objects.filter(certificate_request_status__in=['requested','sent']).select_related('user').order_by('-certificate_requested_at','-pk')[:250]
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
  elif module=='employees': meta=f"{obj.designation or 'Employee'} · {obj.department or 'General'}"; status='Active' if obj.is_active and obj.user.is_active else 'Inactive'; value=f"{obj.assignments.filter(is_active=True).count()} active projects"
  elif module=='messages': meta=f'{obj.name} · {obj.email}'; status='Resolved' if obj.is_resolved else 'Open'
  elif module=='reviews': meta=str(obj.user); status='Approved' if obj.is_approved else 'Needs review'
  elif module=='certificate-requests': meta=f'{obj.user} · {obj.order_id}'; status=obj.get_certificate_request_status_display(); value=obj.certificate_requested_at.strftime('%d %b %Y %H:%M') if obj.certificate_requested_at else '—'
  elif module=='categories': meta=obj.slug; status='Active' if obj.is_active else 'Hidden'; value=f'{obj.projects.count()} projects'
  elif module=='conversations': meta=str(obj.user or 'Guest'); status='Human support' if obj.mode=='human' else 'AI assistant'; value=f'{obj.messages.count()} messages'
  order_pk = None
  if module == 'requests':
   try: order_pk = obj.order.pk
   except Exception: order_pk = None
  elif module == 'certificate-requests':
   order_pk = obj.pk
  rows.append({'pk':obj.pk,'title':title,'meta':meta,'status':status,'value':value,'order_pk':order_pk})
 return render(request,'dashboard/admin_module.html',{'active':module,'module':cfg,'module_key':module,'rows':rows,'total':cfg['model'].objects.count(),'add_url':reverse('control:add',args=[module]),'can_add':module not in {'requests','orders','payments','messages','reviews','conversations','certificate-requests'},'is_employee_workspace':request.is_employee_workspace})

@workspace_access_required
def admin_edit(request,module,pk=None):
 ensure_module_access(request, module)
 cfg=MODULES.get(module)
 if not cfg: raise Http404
 Model=cfg['model']
 obj=get_object_or_404(Model,pk=pk) if pk else None
 exclude=list(cfg.get('exclude',()))
 if module=='users':
  exclude += ['is_superuser','is_staff']
 if module == 'employees':
  class EmployeeProfileForm(ModelForm):
   class Meta:
    model = EmployeeProfile
    fields = ('user', 'designation', 'department', 'is_active', 'joined_at')
   def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields['user'].queryset = User.objects.filter(is_staff=False, is_superuser=False).order_by('name', 'email')
    self.fields['user'].help_text = 'Create the employee login in Users first, then select that non-admin account here.'
  Form = EmployeeProfileForm
 else:
  Form=modelform_factory(Model,exclude=tuple(exclude))
 if module == 'certificate-requests':
  class CertificateRequestForm(ModelForm):
   class Meta:
    model = Order
    fields = ('certificate_request_status',)
   def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.fields['certificate_request_status'].label = 'Certificate delivery status'
  Form = CertificateRequestForm
 form=Form(request.POST or None,request.FILES or None,instance=obj)
 if request.method=='POST' and form.is_valid():
  saved=form.save()
  if module == 'certificate-requests':
   from django.utils import timezone
   if saved.certificate_request_status == 'sent' and not saved.certificate_sent_at:
    saved.certificate_sent_at = timezone.now()
    saved.save(update_fields=['certificate_sent_at', 'updated_at'])
   elif saved.certificate_request_status != 'sent' and saved.certificate_sent_at:
    saved.certificate_sent_at = None
    saved.save(update_fields=['certificate_sent_at', 'updated_at'])
  if module=='users' and not obj and not saved.has_usable_password(): saved.set_unusable_password(); saved.save()
  messages.success(request,f'{cfg["title"][:-1] if cfg["title"].endswith("s") else cfg["title"]} saved successfully.')
  return redirect('control:module',module=module)
 return render(request,'dashboard/admin_form.html',{'active':module,'module':cfg,'module_key':module,'form':form,'editing':bool(obj),'object':obj,'is_employee_workspace':request.is_employee_workspace})

@workspace_access_required
@require_POST
def admin_delete(request,module,pk):
 ensure_module_access(request, module)
 cfg=MODULES.get(module)
 if not cfg: raise Http404
 obj=get_object_or_404(cfg['model'],pk=pk); obj.delete(); messages.success(request,'Item deleted successfully.')
 return redirect('control:module',module=module)


@workspace_access_required
def admin_workforce(request):
    assignments = OrderAssignment.objects.filter(is_active=True).select_related('employee__user', 'order__user').order_by('-assigned_at')
    employee_id = request.GET.get('employee', '').strip()
    status = request.GET.get('status', '').strip()
    search = request.GET.get('q', '').strip()
    if employee_id.isdigit():
        assignments = assignments.filter(employee_id=int(employee_id))
    if status:
        assignments = assignments.filter(order__status=status)
    if search:
        from django.db.models import Q
        assignments = assignments.filter(Q(order__title__icontains=search) | Q(order__order_id__icontains=search) | Q(employee__user__name__icontains=search) | Q(employee__user__email__icontains=search))
    sort = request.GET.get('sort', 'recent')
    sort_map = {'recent': '-assigned_at', 'oldest': 'assigned_at', 'project': 'order__title', 'employee': 'employee__user__name', 'status': 'order__status'}
    assignments = assignments.order_by(sort_map.get(sort, '-assigned_at'))
    return render(request, 'dashboard/admin_workforce.html', {
        'active': 'workforce', 'assignments': assignments[:500],
        'employees': EmployeeProfile.objects.filter(is_active=True, user__is_active=True).select_related('user'),
        'selected_employee': employee_id, 'selected_status': status, 'search': search, 'selected_sort': sort,
        'status_choices': Order.STATUS, 'is_employee_workspace': request.is_employee_workspace,
    })


def admin_entry(request):
    if not request.user.is_authenticated:
        return redirect('/accounts/login/?next=/admin/')
    if not (request.user.is_staff or request.user.is_superuser or EmployeeProfile.objects.filter(user=request.user, is_active=True, user__is_active=True).exists()):
        return redirect('dashboard:home')
    return admin_home(request)


@workspace_access_required
def admin_order_detail(request, pk):
    order = get_object_or_404(Order.objects.select_related('user', 'project', 'request'), pk=pk)
    if request.method == 'POST' and request.POST.get('action') == 'assign_employee':
        employee_ids = request.POST.getlist('employees')
        OrderAssignment.objects.filter(order=order, is_active=True).exclude(employee_id__in=employee_ids).update(is_active=False)
        for employee in EmployeeProfile.objects.filter(pk__in=employee_ids, is_active=True, user__is_active=True):
            OrderAssignment.objects.get_or_create(order=order, employee=employee, is_active=True, defaults={'assigned_by': request.user})
        messages.success(request, 'Project team assignment updated.')
        return redirect('control:order_detail', pk=order.pk)
    return render(request, 'dashboard/admin_order_detail.html', {
        'active': 'orders', 'order': order,
        'payments': order.payments.select_related('user', 'verified_by').order_by('-created_at') if not request.is_employee_workspace else [],
        'updates': order.updates.select_related('created_by').order_by('-created_at'),
        'quotations': order.quotations.order_by('-created_at'),
        'employees': EmployeeProfile.objects.filter(is_active=True, user__is_active=True).select_related('user'),
        'assigned_employee_ids': list(order.employee_assignments.filter(is_active=True).values_list('employee_id', flat=True)),
        'work_updates': order.work_updates.select_related('employee__user').all(),
        'is_employee_workspace': request.is_employee_workspace,
    })


from datetime import date
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.utils.dateparse import parse_date
from accounts.models import EmployeeProfile
from orders.models import Order, OrderAssignment, OrderWorkUpdate

def employee_required(view):
    @login_required(login_url='/accounts/login/')
    def wrapped(request, *args, **kwargs):
        profile = EmployeeProfile.objects.filter(user=request.user, is_active=True, user__is_active=True).first()
        if not profile:
            messages.error(request, 'Employee access is not enabled for this account.')
            return redirect('dashboard:home')
        request.employee_profile = profile
        return view(request, *args, **kwargs)
    return wrapped

@employee_required
def employee_home(request):
    assignments = OrderAssignment.objects.filter(employee=request.employee_profile, is_active=True).select_related('order','order__user','order__project').order_by('-assigned_at')
    return render(request, 'dashboard/employee_home.html', {'employee': request.employee_profile, 'assignments': assignments})

@employee_required
def employee_order(request, order_id):
    assignment = get_object_or_404(OrderAssignment.objects.select_related('order','order__user','order__project','employee'), employee=request.employee_profile, is_active=True, order__order_id=order_id)
    order = assignment.order
    if request.method == 'POST':
        stage = request.POST.get('stage', 'started')
        allowed = {key for key, label in OrderWorkUpdate.STAGES}
        if stage not in allowed: stage = 'started'
        try: progress = max(0, min(100, int(request.POST.get('progress_percent', 0))))
        except (TypeError, ValueError): progress = 0
        delivery = parse_date(request.POST.get('expected_delivery_date', ''))
        message = request.POST.get('message', '').strip()
        visible = request.POST.get('is_customer_visible') == 'on'
        if not message:
            messages.error(request, 'Please add a short work update.')
        elif stage == 'delivered' and not order.payments.filter(status='verified').exists():
            messages.error(request, 'Payment must be verified by Admin before marking this project as delivered.')
        else:
            OrderWorkUpdate.objects.create(order=order, employee=request.employee_profile, stage=stage, progress_percent=progress, expected_delivery_date=delivery, message=message, is_customer_visible=visible)
            order.stage = stage if stage in {'discussed','started','completed','delivered'} else 'started'
            if stage == 'delivered': order.status = 'delivered'
            elif stage == 'completed': order.status = 'completed'
            elif stage in {'started','testing'}: order.status = 'in_progress'
            order.save(update_fields=['stage','status','updated_at'])
            messages.success(request, 'Project progress updated.')
            return redirect('dashboard:employee_order', order_id=order.order_id)
    return render(request, 'dashboard/employee_order.html', {'employee': request.employee_profile, 'order': order, 'updates': order.work_updates.select_related('employee__user').all(), 'stages': OrderWorkUpdate.STAGES})

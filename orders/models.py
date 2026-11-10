from django.conf import settings
from django.db import models
from catalog.models import Project,Category
class ProjectRequest(models.Model):
 REQUEST_TYPES=[('business','Business project request'),('academic_custom','Build your own academic project'),('ready_custom','Ready-made project feature customization')]
 ACADEMIC_TEAM_TYPES=[('single','Single person project'),('group','Group project')]
 request_type=models.CharField(max_length=24,choices=REQUEST_TYPES,default='business',db_index=True)
 academic_team_type=models.CharField(max_length=12,choices=ACADEMIC_TEAM_TYPES,default='single')
 group_size=models.PositiveSmallIntegerField(default=1)
 group_member_names=models.TextField(blank=True,help_text='One student name per line for group certificates.')
 customization_features=models.TextField(blank=True,help_text='Optional features to add to a ready-made project.')
 user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='project_requests'); project=models.ForeignKey(Project,on_delete=models.SET_NULL,null=True,blank=True); title=models.CharField(max_length=200); category=models.ForeignKey(Category,on_delete=models.SET_NULL,null=True,blank=True); required_features=models.TextField(); technologies=models.CharField(max_length=500,blank=True); requirements=models.TextField(blank=True); budget=models.DecimalField(max_digits=10,decimal_places=2,null=True,blank=True); deadline=models.DateField(null=True,blank=True); reference_file=models.FileField(upload_to='requests/',blank=True); created_at=models.DateTimeField(auto_now_add=True)
 def __str__(self): return self.title
class Order(models.Model):
 STAGES=[('discussed','Project Discussed'),('started','Project Started'),('completed','Completed'),('delivered','Delivered')]
 STATUS=[(x,x.replace('_',' ').title()) for x in ['pending','under_review','quotation_sent','awaiting_payment','paid','in_progress','completed','delivered','cancelled']]
 ORDER_TYPES=[('business','Business Project'),('academic','Academic Project Purchase'),('academic_custom','Academic Custom Build')]
 order_type=models.CharField(max_length=24,choices=ORDER_TYPES,default='business',db_index=True)
 project=models.ForeignKey(Project,on_delete=models.SET_NULL,null=True,blank=True,related_name='orders')
 user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name='orders'); request=models.OneToOneField(ProjectRequest,on_delete=models.SET_NULL,null=True,blank=True); order_id=models.CharField(max_length=24,unique=True,editable=False); title=models.CharField(max_length=200); amount=models.DecimalField(max_digits=10,decimal_places=2,default=0); status=models.CharField(max_length=24,choices=STATUS,default='pending'); stage=models.CharField(max_length=16,choices=STAGES,default='discussed',db_index=True); certificate_request_status=models.CharField(max_length=20,choices=[('not_requested','Not requested'),('requested','Requested'),('sent','Sent')],default='not_requested',db_index=True); certificate_requested_at=models.DateTimeField(null=True,blank=True); certificate_sent_at=models.DateTimeField(null=True,blank=True); created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
 def save(self,*a,**k):
  if not self.order_id:
   prefix='CRI-ORD-'
   nums=[]
   for old in Order.objects.filter(order_id__startswith=prefix).values_list('order_id',flat=True):
    tail=old[len(prefix):]
    if tail.isdigit(): nums.append(int(tail))
   candidate=max(nums or [0])+1
   self.order_id=f'{prefix}{candidate:06d}'
   while Order.objects.filter(order_id=self.order_id).exists():
    candidate+=1; self.order_id=f'{prefix}{candidate:06d}'
  if self.pk and self.stage == 'delivered':
   from django.core.exceptions import ValidationError
   if not self.payments.filter(status='verified').exists():
    raise ValidationError('Verify payment before marking this project as delivered.')
  super().save(*a,**k)
  # Keep payment records in sync when an administrator marks an order as paid.
  if self.status == 'paid' and self.pk:
   from django.utils import timezone
   self.payments.exclude(status='verified').update(status='verified', verified_at=timezone.now())
 @property
 def stage_progress(self):
  return {'discussed': 0, 'started': 1, 'completed': 2, 'delivered': 3}.get(self.stage, 0)
 def __str__(self): return self.order_id
class Quotation(models.Model):
 order=models.ForeignKey(Order,on_delete=models.CASCADE,related_name='quotations'); amount=models.DecimalField(max_digits=10,decimal_places=2); notes=models.TextField(blank=True); valid_until=models.DateField(null=True,blank=True); accepted=models.BooleanField(default=False); created_at=models.DateTimeField(auto_now_add=True)
class OrderUpdate(models.Model):
 order=models.ForeignKey(Order,on_delete=models.CASCADE,related_name='updates'); message=models.TextField(); created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True); created_at=models.DateTimeField(auto_now_add=True)


class OrderAssignment(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='employee_assignments')
    employee = models.ForeignKey('accounts.EmployeeProfile', on_delete=models.CASCADE, related_name='assignments')
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_assignments')
    assigned_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-assigned_at']
        constraints = [models.UniqueConstraint(fields=['order', 'employee'], condition=models.Q(is_active=True), name='unique_active_order_employee')]

    def __str__(self):
        return f'{self.order.order_id} → {self.employee}'


class OrderWorkUpdate(models.Model):
    STAGES = [('discussed', 'Project Discussed'), ('started', 'Project Started'), ('testing', 'Testing'), ('completed', 'Completed'), ('delivered', 'Delivered')]
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='work_updates')
    employee = models.ForeignKey('accounts.EmployeeProfile', on_delete=models.SET_NULL, null=True, related_name='work_updates')
    stage = models.CharField(max_length=16, choices=STAGES, default='started')
    progress_percent = models.PositiveSmallIntegerField(default=0)
    expected_delivery_date = models.DateField(null=True, blank=True)
    message = models.TextField()
    is_customer_visible = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.order.order_id} · {self.progress_percent}%'

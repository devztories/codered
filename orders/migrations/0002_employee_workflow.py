import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('orders', '0001_initial'), ('accounts', '0002_employeeprofile')]
    operations = [
        migrations.CreateModel(name='OrderAssignment', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('assigned_at', models.DateTimeField(auto_now_add=True)), ('is_active', models.BooleanField(default=True)),
            ('assigned_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_assignments', to=settings.AUTH_USER_MODEL)),
            ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='accounts.employeeprofile')),
            ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='employee_assignments', to='orders.order')),
        ], options={'ordering': ['-assigned_at']}),
        migrations.AddConstraint(model_name='orderassignment', constraint=models.UniqueConstraint(condition=models.Q(('is_active', True)), fields=('order', 'employee'), name='unique_active_order_employee')),
        migrations.CreateModel(name='OrderWorkUpdate', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('stage', models.CharField(choices=[('discussed','Project Discussed'),('started','Project Started'),('testing','Testing'),('completed','Completed'),('delivered','Delivered')], default='started', max_length=16)),
            ('progress_percent', models.PositiveSmallIntegerField(default=0)), ('expected_delivery_date', models.DateField(blank=True, null=True)), ('message', models.TextField()), ('is_customer_visible', models.BooleanField(default=True)), ('created_at', models.DateTimeField(auto_now_add=True)),
            ('employee', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='work_updates', to='accounts.employeeprofile')),
            ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='work_updates', to='orders.order')),
        ], options={'ordering': ['-created_at']}),
    ]

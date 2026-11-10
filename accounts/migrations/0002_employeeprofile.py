# Generated for employee workspace support.
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('accounts', '0001_initial')]
    operations = [migrations.CreateModel(name='EmployeeProfile', fields=[
        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
        ('employee_code', models.CharField(blank=True, max_length=24, unique=True)),
        ('designation', models.CharField(blank=True, max_length=120)),
        ('department', models.CharField(blank=True, max_length=120)),
        ('is_active', models.BooleanField(default=True)),
        ('joined_at', models.DateField(blank=True, null=True)),
        ('created_at', models.DateTimeField(auto_now_add=True)),
        ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='employee_profile', to=settings.AUTH_USER_MODEL)),
    ], options={'ordering': ['employee_code']})]

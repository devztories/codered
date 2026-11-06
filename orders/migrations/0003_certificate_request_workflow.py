from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("orders", "0002_employee_workflow")]
    operations = [
        migrations.AddField(model_name="order", name="certificate_request_status",
            field=models.CharField(choices=[("not_requested", "Not requested"), ("requested", "Requested"), ("sent", "Sent")], db_index=True, default="not_requested", max_length=20)),
        migrations.AddField(model_name="order", name="certificate_requested_at", field=models.DateTimeField(blank=True, null=True)),
        migrations.AddField(model_name="order", name="certificate_sent_at", field=models.DateTimeField(blank=True, null=True)),
    ]

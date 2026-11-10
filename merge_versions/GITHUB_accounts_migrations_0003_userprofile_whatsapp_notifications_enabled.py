from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0002_employeeprofile")]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="whatsapp_notifications_enabled",
            field=models.BooleanField(
                default=False,
                help_text="Customer has opted in to receive WhatsApp updates.",
            ),
        ),
    ]

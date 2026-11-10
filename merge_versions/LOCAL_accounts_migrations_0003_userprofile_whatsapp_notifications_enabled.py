from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_employeeprofile"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="whatsapp_notifications_enabled",
            field=models.BooleanField(
                default=False,
                help_text="I agree to receive account and project updates on WhatsApp.",
            ),
        ),
    ]

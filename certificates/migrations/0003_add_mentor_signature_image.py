from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("certificates", "0002_certificatedesignsettings")]

    operations = [
        migrations.AddField(
            model_name="certificatedesignsettings",
            name="mentor_signature_image",
            field=models.ImageField(
                blank=True,
                help_text="Upload the project mentor’s signature. A transparent PNG is recommended.",
                upload_to="certificate/signatures/",
            ),
        ),
    ]

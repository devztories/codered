from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("certificates", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="CertificateDesignSettings",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("certificate_heading", models.CharField(default="CERTIFICATE", max_length=80)),
                ("ribbon_text", models.CharField(default="OF PROJECT COMPLETION", max_length=100)),
                ("intro_text", models.CharField(default="THIS IS TO CERTIFY THAT", max_length=120)),
                ("completion_text", models.CharField(default="has successfully completed the project titled", max_length=180)),
                ("body_text", models.TextField(default="at CodeRed Invention, as part of the academic / professional project program. The project was carried out with dedication, technical proficiency, and a commendable level of problem-solving and implementation skills.")),
                ("company_id", models.CharField(default="CRI/2026/0145", max_length=80)),
                ("certificate_prefix", models.CharField(default="CRI-PRJ-", max_length=24)),
                ("issue_date_label", models.CharField(default="DATE OF ISSUE", max_length=60)),
                ("verification_label", models.CharField(default="Verify Certificate", max_length=60)),
                ("mentor_signature_text", models.CharField(default="Project Mentor", max_length=100)),
                ("mentor_title", models.CharField(default="Project Mentor", max_length=100)),
                ("company_name", models.CharField(default="CodeRed Invention", max_length=120)),
                ("website", models.CharField(default="www.coderedinvention.com", max_length=120)),
                ("location", models.CharField(default="Kochi, Kerala, India", max_length=120)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name": "Certificate design settings", "verbose_name_plural": "Certificate design settings"},
        ),
    ]

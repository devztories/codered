from django.conf import settings
from django.db import models
from orders.models import Order

class Certificate(models.Model):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="certificates")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    recipient_name = models.CharField(max_length=150)
    project_name = models.CharField(max_length=200)
    completion_date = models.DateField()
    certificate_id = models.CharField(max_length=32, unique=True, editable=False, blank=True)
    revoked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.certificate_id:
            design = CertificateDesignSettings.objects.filter(pk=1).first()
            prefix = design.certificate_prefix if design else "CRI-PRJ-"
            numbers = []
            for value in Certificate.objects.filter(certificate_id__startswith=prefix).values_list("certificate_id", flat=True):
                tail = value[len(prefix):]
                if tail.isdigit(): numbers.append(int(tail))
            number = max(numbers or [0]) + 1
            self.certificate_id = f"{prefix}{number:06d}"
            while Certificate.objects.filter(certificate_id=self.certificate_id).exists():
                number += 1
                self.certificate_id = f"{prefix}{number:06d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.certificate_id


class CertificateDesignSettings(models.Model):
    """Single admin-managed configuration for every generated certificate."""
    certificate_heading = models.CharField(max_length=80, default="CERTIFICATE")
    ribbon_text = models.CharField(max_length=100, default="OF PROJECT COMPLETION")
    intro_text = models.CharField(max_length=120, default="THIS IS TO CERTIFY THAT")
    completion_text = models.CharField(max_length=180, default="has successfully completed the project titled")
    body_text = models.TextField(default="at CodeRed Invention, as part of the academic / professional project program. The project was carried out with dedication, technical proficiency, and a commendable level of problem-solving and implementation skills.")
    company_id = models.CharField(max_length=80, default="CRI/2026/0145")
    certificate_prefix = models.CharField(max_length=24, default="CRI-PRJ-")
    issue_date_label = models.CharField(max_length=60, default="DATE OF ISSUE")
    verification_label = models.CharField(max_length=60, default="Verify Certificate")
    mentor_signature_text = models.CharField(max_length=100, default="Project Mentor")
    mentor_signature_image = models.ImageField(
        upload_to="certificate/signatures/", blank=True,
        help_text="Upload the project mentor’s signature. A transparent PNG is recommended.",
    )
    mentor_title = models.CharField(max_length=100, default="Project Mentor")
    company_name = models.CharField(max_length=120, default="CodeRed Invention")
    website = models.CharField(max_length=120, default="www.coderedinvention.com")
    location = models.CharField(max_length=120, default="Kochi, Kerala, India")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Certificate design settings"
        verbose_name_plural = "Certificate design settings"

    def __str__(self):
        return "Certificate design settings"

    @classmethod
    def current(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

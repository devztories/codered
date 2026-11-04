from django.db import models
class ContactMessage(models.Model):
 name=models.CharField(max_length=120); email=models.EmailField(); phone=models.CharField(max_length=20,blank=True); subject=models.CharField(max_length=180); message=models.TextField(); is_resolved=models.BooleanField(default=False); created_at=models.DateTimeField(auto_now_add=True)
 def __str__(self): return self.subject
class SocialLink(models.Model):
 PLATFORM=[(x,x.title()) for x in ['instagram','facebook','linkedin','youtube','github','whatsapp','telegram']]
 platform=models.CharField(max_length=20,choices=PLATFORM,unique=True); url=models.URLField(); is_active=models.BooleanField(default=True)
class SiteSettings(models.Model):
 company_name=models.CharField(max_length=120,default='CODERED INVENTIONS'); tagline=models.CharField(max_length=200,default='Build. Innovate. Deliver.'); logo=models.ImageField(upload_to='branding/',blank=True); about_text=models.TextField(blank=True); contact_email=models.EmailField(blank=True); phone=models.CharField(max_length=30,blank=True); whatsapp_number=models.CharField(max_length=30,blank=True); updated_at=models.DateTimeField(auto_now=True)

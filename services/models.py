from django.db import models
from django.utils.text import slugify
class Service(models.Model):
 title=models.CharField(max_length=160); slug=models.SlugField(unique=True,blank=True); description=models.TextField(); icon=models.CharField(max_length=60,default='fa-code'); order=models.PositiveIntegerField(default=0); is_published=models.BooleanField(default=True)
 def save(self,*a,**k): self.slug=slugify(self.slug or self.title); super().save(*a,**k)
 def __str__(self): return self.title
 class Meta: ordering=['order','title']

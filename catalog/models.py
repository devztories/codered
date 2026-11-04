from django.db import models
from django.utils.text import slugify
class Category(models.Model):
 name=models.CharField(max_length=120,unique=True); slug=models.SlugField(unique=True,blank=True); description=models.TextField(blank=True); order=models.PositiveIntegerField(default=0); is_active=models.BooleanField(default=True)
 def save(self,*a,**k): self.slug=slugify(self.slug or self.name); super().save(*a,**k)
 def __str__(self): return self.name
 class Meta: ordering=['order','name']
class SubCategory(models.Model):
 category=models.ForeignKey(Category,on_delete=models.CASCADE,related_name='subcategories'); name=models.CharField(max_length=120); slug=models.SlugField(blank=True); order=models.PositiveIntegerField(default=0); is_active=models.BooleanField(default=True)
 def save(self,*a,**k): self.slug=slugify(self.slug or self.name); super().save(*a,**k)
 def __str__(self): return f'{self.category}: {self.name}'
 class Meta: unique_together=[('category','name')]; ordering=['order','name']
class Project(models.Model):
 PROJECT_TYPES=[('business','Business Project'),('academic','Academic Project')]
 project_type=models.CharField(max_length=20,choices=PROJECT_TYPES,default='business',db_index=True)
 is_ready_made=models.BooleanField(default=False,help_text='Enable direct purchase for a ready-made academic project.')
 allow_feature_customization=models.BooleanField(default=True,help_text='Allow customers to request additional features.')
 name=models.CharField(max_length=200); slug=models.SlugField(unique=True,blank=True); short_description=models.CharField(max_length=300); description=models.TextField(); cover_image=models.ImageField(upload_to='projects/',blank=True); category=models.ForeignKey(Category,on_delete=models.PROTECT,related_name='projects'); subcategory=models.ForeignKey(SubCategory,on_delete=models.SET_NULL,null=True,blank=True); technologies=models.CharField(max_length=500,help_text='Comma-separated'); features=models.TextField(blank=True); demo_url=models.URLField(blank=True); github_url=models.URLField(blank=True); price=models.DecimalField(max_digits=10,decimal_places=2,default=0); customization_available=models.BooleanField(default=True); is_published=models.BooleanField(default=False); created_at=models.DateTimeField(auto_now_add=True)
 def save(self,*a,**k): self.slug=slugify(self.slug or self.name); super().save(*a,**k)
 def __str__(self): return self.name
class ProjectImage(models.Model):
 project=models.ForeignKey(Project,on_delete=models.CASCADE,related_name='images'); image=models.ImageField(upload_to='project-gallery/'); caption=models.CharField(max_length=200,blank=True); order=models.PositiveIntegerField(default=0)

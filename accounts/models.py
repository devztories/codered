from django.contrib.auth.models import AbstractUser,BaseUserManager
from django.db import models
class UserManager(BaseUserManager):
 use_in_migrations=True
 def _create_user(self,email,phone_number,password,**extra):
  if not email and not phone_number: raise ValueError('Email or phone is required')
  email=self.normalize_email(email) if email else None
  user=self.model(email=email,phone_number=phone_number,**extra); user.set_password(password); user.save(using=self._db); return user
 def create_user(self,email=None,phone_number=None,password=None,**extra): extra.setdefault('is_staff',False); extra.setdefault('is_superuser',False); return self._create_user(email,phone_number,password,**extra)
 def create_superuser(self,email=None,phone_number=None,password=None,**extra): extra.setdefault('is_staff',True); extra.setdefault('is_superuser',True); extra.setdefault('is_active',True); return self._create_user(email,phone_number,password,**extra)
class User(AbstractUser):
 username=None
 email=models.EmailField(unique=True,null=True,blank=True)
 phone_number=models.CharField(max_length=20,unique=True,null=True,blank=True)
 name=models.CharField(max_length=150,blank=True)
 USERNAME_FIELD='email'; REQUIRED_FIELDS=[]; objects=UserManager()
 def __str__(self): return self.email or self.phone_number or self.name
class UserProfile(models.Model):
 user=models.OneToOneField(User,on_delete=models.CASCADE,related_name='profile'); address=models.TextField(blank=True); city=models.CharField(max_length=100,blank=True); state=models.CharField(max_length=100,blank=True); avatar=models.ImageField(upload_to='avatars/',blank=True); created_at=models.DateTimeField(auto_now_add=True)

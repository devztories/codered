from django.contrib.auth.backends import ModelBackend
from .models import User
class EmailOrPhoneBackend(ModelBackend):
 def authenticate(self,request,username=None,password=None,**kwargs):
  login=username or kwargs.get('email') or kwargs.get('phone_number')
  if not login or not password: return None
  try: user=User.objects.get(email__iexact=login) if '@' in login else User.objects.get(phone_number=login)
  except User.DoesNotExist: User().set_password(password); return None
  return user if user.check_password(password) and self.user_can_authenticate(user) else None

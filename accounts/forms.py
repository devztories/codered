from django import forms
from django.contrib.auth.forms import UserCreationForm,AuthenticationForm
from .models import User
class RegisterForm(UserCreationForm):
 class Meta: model=User; fields=('name','email','phone_number')
 def clean(self):
  d=super().clean()
  if not d.get('email') and not d.get('phone_number'): raise forms.ValidationError('Provide an email or phone number.')
  return d
class LoginForm(AuthenticationForm):
 username=forms.CharField(label='Email or phone number')

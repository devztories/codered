from django import forms
from django.contrib.auth.forms import UserCreationForm,AuthenticationForm
from .models import User
class RegisterForm(UserCreationForm):
 class Meta: model=User; fields=('name','email','phone_number')
 def __init__(self, *args, **kwargs):
  super().__init__(*args, **kwargs)
  self.fields['phone_number'].required = True
  self.fields['phone_number'].widget.attrs.update({'required': 'required', 'inputmode': 'tel', 'autocomplete': 'tel', 'placeholder': 'Your mobile number'})
 def clean_phone_number(self):
  value = (self.cleaned_data.get('phone_number') or '').strip()
  if not value: raise forms.ValidationError('Phone number is required to create an account.')
  return value
class LoginForm(AuthenticationForm):
 username=forms.CharField(label='Email or phone number')

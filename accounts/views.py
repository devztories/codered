
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView
from django.shortcuts import render, redirect
from django.contrib import messages
from django import forms

from .forms import RegisterForm, LoginForm
from .models import UserProfile


class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('address', 'city', 'state', 'avatar')


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard:home')

    form = RegisterForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(
            request,
            user,
            backend='accounts.backends.EmailOrPhoneBackend'
        )
        return redirect('dashboard:home')

    return render(
        request,
        'accounts/form.html',
        {
            'form': form,
            'title': 'Create your account'
        }
    )


def login_view(request):
    if request.user.is_authenticated:
        from .models import EmployeeProfile

        if request.user.is_staff or EmployeeProfile.objects.filter(
            user=request.user,
            is_active=True,
            user__is_active=True
        ).exists():
            return redirect('/admin/')

        return redirect('dashboard:home')

    form = LoginForm(request, data=request.POST or None)

    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)

        if user.is_staff:
            return redirect('/admin/')

        from .models import EmployeeProfile

        if EmployeeProfile.objects.filter(
            user=user,
            is_active=True,
            user__is_active=True
        ).exists():
            return redirect('/admin/')

        return redirect(
            request.GET.get('next') or 'dashboard:home'
        )

    return render(
        request,
        'accounts/form.html',
        {
            'form': form,
            'title': 'Welcome back'
        }
    )


def logout_view(request):
    if request.method == 'POST':
        logout(request)

    return redirect('home')


@login_required
def profile(request):
    profile, _ = UserProfile.objects.get_or_create(
        user=request.user
    )

    form = ProfileForm(
        request.POST or None,
        request.FILES or None,
        instance=profile,
    )

    if request.method == 'POST' and form.is_valid():
        form.save()

        messages.success(
            request,
            "Profile updated."
        )

        return redirect('dashboard:home')

    return render(
        request,
        'accounts/form.html',
        {
            'form': form,
            'title': 'My profile',
            'skip_back_after_submit': True,
        }
    )

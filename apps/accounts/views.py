from django.shortcuts import render, redirect
from django.views.generic import TemplateView, View
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages


class LandingView(TemplateView):
    """صفحه فرود"""
    template_name = 'accounts/landing.html'
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')
        return super().dispatch(request, *args, **kwargs)


class LoginView(View):
    """ورود به سیستم"""
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')
        form = AuthenticationForm()
        return render(request, 'accounts/login.html', {'form': form})
    
    def post(self, request):
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'خوش آمدید {user.get_short_name()} عزیز')
            
            # هدایت بر اساس نقش
            if user.is_super_manager or user.is_club_manager:
                return redirect('accounts:dashboard')
            return redirect('accounts:dashboard')
        
        messages.error(request, 'شماره همراه یا گذرواژه اشتباه است')
        return render(request, 'accounts/login.html', {'form': form})


class LogoutView(View):
    """خروج از سیستم"""
    
    def get(self, request):
        logout(request)
        return redirect('accounts:landing')


class DashboardView(LoginRequiredMixin, TemplateView):
    """پیشخوان"""
    template_name = 'accounts/dashboard.html'

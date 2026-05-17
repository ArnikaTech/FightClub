from django.shortcuts import render, redirect
from django.views.generic import TemplateView, View
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
import jdatetime
from apps.students.models import Student, Attendance


class LandingView(TemplateView):
    template_name = 'accounts/landing.html'
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')
        return super().dispatch(request, *args, **kwargs)


class LoginView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('accounts:dashboard')
        return render(request, 'accounts/login.html')
    
    def post(self, request):
        phone = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=phone, password=password)
        
        if user:
            login(request, user)
            messages.success(request, f'خوش آمدید {user.get_short_name()} عزیز')
            return redirect('accounts:dashboard')
        
        messages.error(request, 'شماره موبایل یا رمز عبور اشتباه است')
        return render(request, 'accounts/login.html')


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('accounts:landing')


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = jdatetime.date.today()
        
        # همه آمارها با پیش‌فرض ۰
        context['total_students'] = Student.objects.filter(is_active=True).count() or 0
        context['present_today'] = Attendance.objects.filter(date=today, status='present').count() or 0
        context['absent_today'] = Attendance.objects.filter(date=today, status='absent').count() or 0
        
        # تولدهای امروز
        context['birthdays_today'] = Student.objects.filter(
            is_active=True,
            birth_date__month=today.month,
            birth_date__day=today.day
        ).count() or 0
        
        # غیبت متوالی (۳+)
        critical = 0
        for s in Student.objects.filter(is_active=True):
            recent = list(s.attendances.order_by('-date')[:3])
            if len(recent) == 3 and all(a.status == 'absent' for a in recent):
                critical += 1
        context['critical_absences'] = critical
        
        # بیمه نزدیک انقضا (۷ روز)
        expiring = 0
        for s in Student.objects.filter(is_active=True):
            days = s.insurance_days_left()
            if days is not None and days <= 7:
                expiring += 1
        context['expiring_insurance'] = expiring
        
        return context

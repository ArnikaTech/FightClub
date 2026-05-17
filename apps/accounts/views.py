from django.shortcuts import render, redirect
from django.views.generic import TemplateView, View
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
import jdatetime
from apps.students.models import Student, Attendance
from apps.clubs.models import Club


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
        user = self.request.user
        today = jdatetime.date.today()
        
        club_id = self.request.GET.get('club_id')
        
        if user.is_super_manager:
            clubs = Club.objects.filter(is_active=True)
            if club_id:
                students = Student.objects.filter(club_id=club_id, is_active=True)
                selected_club = Club.objects.get(pk=club_id) if Club.objects.filter(pk=club_id).exists() else None
            else:
                students = Student.objects.filter(is_active=True)
                selected_club = None
        elif user.is_club_manager:
            clubs = Club.objects.filter(memberships__user=user, is_active=True)
            students = Student.objects.filter(club__in=clubs, is_active=True).distinct()
            selected_club = None
        else:
            clubs = Club.objects.none()
            students = Student.objects.none()
            selected_club = None
        
        context['clubs'] = clubs
        context['selected_club'] = selected_club
        
        # آمار با پیش‌فرض ۰
        context['total_students'] = students.count() or 0
        context['present_today'] = Attendance.objects.filter(
            student__in=students, date=today, status='present'
        ).count() or 0
        context['absent_today'] = Attendance.objects.filter(
            student__in=students, date=today, status='absent'
        ).count() or 0
        
        # تولدها
        context['birthdays_today'] = students.filter(
            birth_date__month=today.month,
            birth_date__day=today.day
        ).count() or 0
        
        # غیبت متوالی
        critical = 0
        for s in students:
            recent = list(s.attendances.order_by('-date')[:3])
            if len(recent) == 3 and all(a.status == 'absent' for a in recent):
                critical += 1
        context['critical_absences'] = critical or 0
        
        # بیمه نزدیک انقضا
        expiring = 0
        for s in students:
            days = s.insurance_days_left()
            if days is not None and days <= 7:
                expiring += 1
        context['expiring_insurance'] = expiring or 0
        
        return context

from django.shortcuts import render, redirect
from django.views.generic import TemplateView, View
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
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
            return redirect('accounts:dashboard')
        
        list(messages.get_messages(request))
        messages.error(request, 'شماره همراه یا گذرواژه اشتباه است.')
        return render(request, 'accounts/login.html')


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
        context['total_students'] = students.count() or 0
        context['present_today'] = Attendance.objects.filter(student__in=students, date=today, status='present').count() or 0
        context['absent_today'] = Attendance.objects.filter(student__in=students, date=today, status='absent').count() or 0
        context['birthdays_today'] = students.filter(birth_date__month=today.month, birth_date__day=today.day).count() or 0
        
        critical = 0
        for s in students:
            recent = list(s.attendances.order_by('-date')[:3])
            if len(recent) == 3 and all(a.status == 'absent' for a in recent):
                critical += 1
        context['critical_absences'] = critical or 0
        
        expiring = 0
        for s in students:
            days = s.insurance_days_left()
            if days is not None and days <= 7:
                expiring += 1
        context['expiring_insurance'] = expiring or 0
        
        return context


class LogoutView(View):
    def get(self, request):
        logout(request)
        return redirect('accounts:landing')


class ProfileView(LoginRequiredMixin, TemplateView):
    """پروفایل کاربر"""
    template_name = 'accounts/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        try:
            student = user.student_profile
            context['student'] = student
        except:
            context['student'] = None
        
        if user.is_super_manager or user.is_club_manager:
            context['managed_clubs'] = Club.objects.filter(memberships__user=user, is_active=True)
        
        return context


class ProfileEditView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'accounts/profile_edit.html')
    
    def post(self, request):
        user = request.user
        
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        
        if not first_name or not last_name:
            messages.error(request, 'نام و نام خانوادگی الزامی است')
            return redirect('accounts:profile_edit')
        
        user.first_name = first_name
        user.last_name = last_name
        user.national_code = request.POST.get('national_code', '').strip() or None
        
        # تاریخ تولد
        birth_date_str = request.POST.get('birth_date', '').strip()
        if birth_date_str:
            try:
                parts = list(map(int, birth_date_str.replace('/', '-').split('-')))
                user.birth_date = jdatetime.date(*parts)
            except:
                messages.error(request, 'تاریخ تولد نامعتبر است')
                return redirect('accounts:profile_edit')
        
        avatar = request.FILES.get('avatar')
        if avatar:
            user.avatar = avatar
        
        if user.is_super_manager:
            user.is_club_manager = request.POST.get('is_club_manager') == 'on'
            user.is_instructor = request.POST.get('is_instructor') == 'on'
        
        user.save()
        messages.success(request, 'پروفایل بروزرسانی شد')
        return redirect('accounts:profile')


class PasswordChangeView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'accounts/password_change.html')
    
    def post(self, request):
        user = request.user
        current = request.POST.get('current_password', '')
        new = request.POST.get('new_password', '')
        confirm = request.POST.get('confirm_password', '')
        
        if not user.check_password(current):
            messages.error(request, 'رمز عبور فعلی اشتباه است')
            return redirect('accounts:password_change')
        
        if len(new) < 4:
            messages.error(request, 'رمز عبور جدید باید حداقل ۴ کاراکتر باشد')
            return redirect('accounts:password_change')
        
        if new != confirm:
            messages.error(request, 'رمز عبور جدید با تکرار آن مطابقت ندارد')
            return redirect('accounts:password_change')
        
        user.set_password(new)
        user.save()
        
        # حفظ session - کاربر رو خارج نمی‌کنه
        update_session_auth_hash(request, user)
        
        messages.success(request, 'رمز عبور با موفقیت تغییر کرد')
        return redirect('accounts:profile')

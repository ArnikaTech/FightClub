from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, DetailView, View
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.urls import reverse
from django.db import models

import jdatetime
from apps.students.models import Student, Attendance
from apps.clubs.models import Club
from .models import User, Message


def managed_clubs_for(user):
    if user.is_super_manager:
        return Club.objects.all()
    if user.is_club_manager or user.is_instructor:
        return Club.objects.filter(memberships__user=user, memberships__is_active=True).distinct()
    return Club.objects.none()


def visible_students_for(user):
    if user.is_super_manager:
        return Student.objects.all()
    if user.is_club_manager or user.is_instructor:
        return Student.objects.filter(club__in=managed_clubs_for(user)).distinct()
    try:
        return Student.objects.filter(pk=user.student_profile.pk)
    except Student.DoesNotExist:
        return Student.objects.none()


def allowed_receivers_for(user):
    if user.is_super_manager:
        return User.objects.filter(is_active=True)
    if user.is_club_manager or user.is_instructor:
        clubs = managed_clubs_for(user)
        return User.objects.filter(
            models.Q(student_profile__club__in=clubs) |
            models.Q(club_memberships__club__in=clubs),
            is_active=True
        ).distinct()
    clubs = Club.objects.filter(students__user=user)
    return User.objects.filter(club_memberships__club__in=clubs, is_active=True).distinct()


def visible_messages_for(user):
    return Message.objects.filter(models.Q(sender=user) | models.Q(receiver=user))


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
                selected_club = clubs.filter(pk=club_id).first()
                students = Student.objects.filter(club=selected_club, is_active=True) if selected_club else Student.objects.none()
            else:
                students = Student.objects.filter(is_active=True)
                selected_club = None
        elif user.is_club_manager:
            clubs = managed_clubs_for(user).filter(is_active=True)
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
    
    def post(self, request):
        logout(request)
        return redirect('accounts:landing')


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        try:
            student = user.student_profile
            context['student'] = student
        except:
            context['student'] = None
        
        # باشگاه‌های تحت مدیریت
        if user.is_super_manager:
            # مدیر کل همه باشگاه‌های فعال رو می‌بینه
            context['managed_clubs'] = Club.objects.filter(is_active=True)
        else:
            # بقیه فقط باشگاه‌هایی که عضویت دارن
            context['managed_clubs'] = Club.objects.filter(
                memberships__user=user,
                memberships__is_active=True,
                is_active=True
            ).distinct()
        
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


class InboxView(LoginRequiredMixin, ListView):
    template_name = 'accounts/inbox.html'
    context_object_name = 'messages'
    paginate_by = 20
    
    def get_queryset(self):
        user = self.request.user
        if user.is_super_manager:
            return Message.objects.filter(receiver=user).select_related('sender', 'student')
        return Message.objects.filter(receiver=user).select_related('sender', 'student')


class SentView(LoginRequiredMixin, ListView):
    template_name = 'accounts/sent.html'
    context_object_name = 'message_list'
    paginate_by = 20
    
    def get_queryset(self):
        return Message.objects.filter(sender=self.request.user).select_related('receiver', 'student')


class ComposeView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        return render(request, 'accounts/compose.html', {'receivers': allowed_receivers_for(user)})
    
    def post(self, request):
        receiver_id = request.POST.get('receiver')
        student_id = request.POST.get('student')
        subject = request.POST.get('subject', '').strip()
        body = request.POST.get('body', '').strip()
        
        if receiver_id and subject and body:
            receiver = get_object_or_404(allowed_receivers_for(request.user), pk=receiver_id)
            student = None
            if student_id:
                student = get_object_or_404(visible_students_for(request.user), pk=student_id)
            Message.objects.create(
                sender=request.user,
                receiver=receiver,
                student=student,
                subject=subject,
                body=body
            )
            messages.success(request, 'پیام ارسال شد')
            return redirect('accounts:sent_messages')
        
        messages.error(request, 'همه فیلدها الزامی است')
        return redirect('accounts:compose_message')


class ThreadView(LoginRequiredMixin, DetailView):
    model = Message
    template_name = 'accounts/thread.html'
    context_object_name = 'message'

    def get_queryset(self):
        return visible_messages_for(self.request.user)
    
    def get_object(self):
        msg = super().get_object()
        # فقط گیرنده mark as read کنه
        if msg.receiver == self.request.user and not msg.is_read:
            msg.is_read = True
            msg.save()
        return msg
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        msg = self.object
        
        thread = []
        current = msg
        while current.parent:
            current = current.parent
        thread.append(current)
        for reply in current.replies.all():
            thread.append(reply)
        
        context['thread'] = thread
        return context


class ReplyView(LoginRequiredMixin, View):
    def post(self, request, pk):
        parent = get_object_or_404(visible_messages_for(request.user), pk=pk)
        body = request.POST.get('body', '').strip()
        
        if body:
            Message.objects.create(
                sender=request.user,
                receiver=parent.sender,
                student=parent.student,
                subject=f"پاسخ: {parent.subject}",
                body=body,
                parent=parent
            )
        return redirect(f'{reverse("accounts:message_thread", kwargs={"pk": pk})}?sent=1')


class BulkMessageView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        
        # دریافت مخاطبان بر اساس دسترسی
        if user.is_super_manager:
            students = Student.objects.filter(is_active=True).select_related('user', 'club')
            coaches = User.objects.filter(is_instructor=True, is_active=True)
            managers = User.objects.filter(is_club_manager=True, is_active=True)
        elif user.is_club_manager:
            clubs = managed_clubs_for(user).filter(is_active=True)
            students = Student.objects.filter(club__in=clubs, is_active=True).select_related('user', 'club')
            coaches = User.objects.filter(club_memberships__club__in=clubs, is_instructor=True, is_active=True).distinct()
            managers = User.objects.none()
        elif user.is_instructor:
            clubs = managed_clubs_for(user).filter(is_active=True)
            students = Student.objects.filter(club__in=clubs, is_active=True).select_related('user', 'club')
            coaches = User.objects.none()
            managers = User.objects.none()
        else:
            students = Student.objects.none()
            coaches = User.objects.none()
            managers = User.objects.none()
        
        return render(request, 'accounts/bulk_message.html', {
            'students': students,
            'coaches': coaches,
            'managers': managers,
        })
    
    def post(self, request):
        student_ids = request.POST.getlist('students')
        coach_ids = request.POST.getlist('coaches')
        manager_ids = request.POST.getlist('managers')
        subject = request.POST.get('subject', '').strip()
        body = request.POST.get('body', '').strip()
        
        if not subject or not body:
            messages.error(request, 'موضوع و متن پیام الزامی است')
            return redirect('accounts:bulk_message')
        
        count = 0
        
        # ارسال به هنرجویان
        for student_id in student_ids:
            student = get_object_or_404(visible_students_for(request.user), pk=student_id)
            Message.objects.create(sender=request.user, receiver=student.user, student=student, subject=subject, body=body)
            count += 1
            
            # به والدین هنرجو هم بفرست
            for contact in student.contacts.filter(contact_type='parent'):
                parent_user = User.objects.filter(phone=contact.phone).first()
                if parent_user:
                    Message.objects.create(sender=request.user, receiver=parent_user, student=student, subject=subject, body=body)
        
        # ارسال به مربیان
        for coach_id in coach_ids:
            coach = get_object_or_404(allowed_receivers_for(request.user), pk=coach_id)
            Message.objects.create(sender=request.user, receiver=coach, subject=subject, body=body)
            count += 1
        
        # ارسال به مدیران
        for manager_id in manager_ids:
            manager = get_object_or_404(allowed_receivers_for(request.user), pk=manager_id)
            Message.objects.create(sender=request.user, receiver=manager, subject=subject, body=body)
            count += 1
        
        messages.success(request, f'پیام به {count} نفر ارسال شد')
        return redirect('accounts:sent_messages')
